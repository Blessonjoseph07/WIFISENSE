"""
Detection over stored CSI packets (RawCsiTelemetry).

Pipeline:  authenticated /sensing/ingest  ->  RawCsiTelemetry (device-derived provenance)
           ->  windows of packets  ->  csi_features  ->  fall_model  ->  SensingEvent (same provenance)

Honesty rules enforced here
  * Detection only runs for devices whose provenance is `dataset` or `live`. DEMO (`simulated`) devices never get a
    model result, so a demo value can never be mistaken for a measurement.
  * The event keeps the device's provenance, so the UI can say DATASET REPLAY or LIVE HARDWARE truthfully.
  * The model was trained on one dataset (see app/ml/wifall_rf_v2.json). It only accepts that CSI format
    (52 subcarriers as 104 I/Q numbers). Anything else is skipped, never guessed.
  * The score is an uncalibrated heuristic. A positive result is a POSSIBLE fall that needs human verification.
  * DATASET REPLAY never raises alerts or notifications: replayed history must not page anyone.
    LIVE HARDWARE may raise a "Possible fall" alert, which always requires verification (see schemas.AlertOut).
  * Ground-truth labels are never read from packets (they are rejected at ingest).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import update
from sqlmodel import Session, select

from app.core.config import settings
from app.models.entities import ActivityType, Alert, RawCsiTelemetry, Room, SensingDevice, SensingEvent
from app.services import fall_model
from app.services.csi_features import IQ_LEN, MIN_PACKETS, extract_features

MODEL_NAME = "wifall_rf_v2"
WINDOW_PACKETS = 300          # slightly longer than the longest training clip (285), so replayed clips are never split
MIN_WINDOW_PACKETS = MIN_PACKETS
SKIPPED = -1
DETECTABLE_SOURCES = ("dataset", "live")
ALERT_DEDUPE_SECONDS = 120

ACT_POSSIBLE_FALL = ("Possible_Fall", "CRITICAL")
ACT_NO_FALL = ("No_Fall_Pattern", "STATUS")


def signal_quality(rssi: List[float], noise: List[float], seqs: List[int]) -> Dict[str, Any]:
    """Heuristic 0-100 quality of the window. NOT validated against detection accuracy.

    60% from the signal-to-noise margin (10 dB scores 0, 40 dB or more scores 1) and 40% from packet completeness
    (packets received versus the sequence-number span). Unknown noise floor means unknown quality (None)."""
    out: Dict[str, Any] = {"snr_db": None, "completeness": None, "quality": None}
    if seqs and all(s is not None for s in seqs):
        span = max(seqs) - min(seqs) + 1
        out["completeness"] = round(min(1.0, len(seqs) / span), 3) if span > 0 else None
    if noise and rssi:
        snr = float(np.median(rssi) - np.median(noise))
        out["snr_db"] = round(snr, 1)
        snr_score = min(1.0, max(0.0, (snr - 10.0) / 30.0))
        completeness = out["completeness"] if out["completeness"] is not None else 1.0
        out["quality"] = int(round(100 * (0.6 * snr_score + 0.4 * completeness)))
    return out


def _iq_row(rec: RawCsiTelemetry) -> Optional[List[float]]:
    data = rec.csi_data or {}
    iq = data.get("iq") if isinstance(data, dict) else None
    if not isinstance(iq, list) or len(iq) != IQ_LEN:
        return None
    try:
        return [float(v) for v in iq]
    except (TypeError, ValueError):
        return None


def _activity(session: Session, spec) -> ActivityType:
    name, category = spec
    act = session.exec(select(ActivityType).where(ActivityType.name == name)).first()
    if not act:
        act = ActivityType(name=name, category=category)
        session.add(act)
        session.commit()
        session.refresh(act)
    return act


def pending_packets(session: Session, device_id: str, limit: int = 5000) -> List[RawCsiTelemetry]:
    return session.exec(
        select(RawCsiTelemetry)
        .where(RawCsiTelemetry.device_id == device_id, RawCsiTelemetry.event_id.is_(None))
        .order_by(RawCsiTelemetry.id)
        .limit(limit)
    ).all()


def _mark(session: Session, rows: List[RawCsiTelemetry], value: int) -> None:
    for r in rows:
        r.event_id = value
        session.add(r)
    session.commit()


def _raise_possible_fall(session: Session, device: SensingDevice, event: SensingEvent, score: float,
                         quality: Optional[int]) -> Optional[Alert]:
    """LIVE HARDWARE only. One open alert per room per ALERT_DEDUPE_SECONDS. Never notifies anyone by itself."""
    if device.allowed_source != "live":
        return None
    room = session.get(Room, device.room_id)
    since = datetime.now(timezone.utc) - timedelta(seconds=ALERT_DEDUPE_SECONDS)
    recent = session.exec(
        select(Alert).where(
            Alert.room_id == device.room_id, Alert.event_type == "Fall_Detected", Alert.source == "live",
            Alert.status.in_(["new", "acknowledged", "responding"]), Alert.created_at >= since,
        )
    ).first()
    if recent:
        return None
    alert = Alert(
        room_id=device.room_id, event_type="Fall_Detected", severity="WARNING",
        message=f"Possible fall in {room.name if room else 'room'} [LIVE HARDWARE] - verification required",
        status="new", source="live", device_id=device.id, confidence=score, signal_quality=quality,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


def run_detection(session: Session, device: SensingDevice, flush: bool = False) -> Dict[str, Any]:
    """Turn pending packets into detection events. `flush` also processes a final partial window (>= MIN packets)."""
    result: Dict[str, Any] = {"detections": [], "note": None}
    if device.allowed_source not in DETECTABLE_SOURCES:
        result["note"] = "No detection for DEMO devices: demo values are never presented as measurements."
        return result
    if device.allowed_source == "live" and not settings.LIVE_FALL_DETECTION:
        # Not analysed, so mark the packets processed: otherwise they would stay "pending" and never age out of the table.
        session.exec(update(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device.id, RawCsiTelemetry.event_id.is_(None))
                     .values(event_id=SKIPPED))
        session.commit()
        result["note"] = ("Fall detection is switched off for live hardware: the model was trained on a public dataset and has not "
                          "been validated in this room. Presence and movement are reported instead.")
        return result
    if fall_model.model_info().get("available") is not True:
        result["note"] = "Detection model unavailable; packets were stored and remain pending."
        return result

    rows = pending_packets(session, device.id)
    while rows:
        if len(rows) >= WINDOW_PACKETS:
            block, rows = rows[:WINDOW_PACKETS], rows[WINDOW_PACKETS:]
        elif flush:
            block, rows = rows, []
            if len(block) < MIN_WINDOW_PACKETS:
                _mark(session, block, SKIPPED)
                result["note"] = f"Fewer than {MIN_WINDOW_PACKETS} packets in the last window: not enough to analyse."
                continue
        else:
            break

        parsed = [(r, _iq_row(r)) for r in block]
        usable = [(r, iq) for r, iq in parsed if iq is not None]
        unusable = [r for r, iq in parsed if iq is None]
        if unusable:
            _mark(session, unusable, SKIPPED)
        if len(usable) < MIN_WINDOW_PACKETS:
            _mark(session, [r for r, _ in usable], SKIPPED)
            result["note"] = ("CSI format not supported by the detection model (needs 52 subcarriers as 104 I/Q "
                              "numbers in csi_data.iq). Packets are stored but not analysed.")
            continue

        recs = [r for r, _ in usable]
        iq = np.array([v for _, v in usable], dtype=np.float32)
        try:
            names, vec = extract_features(iq)
        except ValueError as exc:
            _mark(session, recs, SKIPPED)
            result["note"] = f"Window could not be analysed: {exc}"
            continue
        score = fall_model.fall_score(vec)
        info = fall_model.model_info()
        threshold = float(info.get("decision_threshold", fall_model.FALL_SCORE_THRESHOLD))
        suspected = score >= threshold

        q = signal_quality([float(r.rssi) for r in recs], [float(r.noise_floor) for r in recs if r.noise_floor is not None],
                           [r.sequence_number for r in recs])
        act = _activity(session, ACT_POSSIBLE_FALL if suspected else ACT_NO_FALL)
        confidence = score if suspected else 1.0 - score
        event = SensingEvent(
            device_id=device.id, room_id=device.room_id,
            rssi=int(round(float(np.median([r.rssi for r in recs])))),
            subcarrier_count=recs[0].subcarrier_count, signal_quality=q["quality"],
            event_type="DetectionWindow", raw_csi_payload_path=None,
            extracted_features={
                "model": MODEL_NAME, "fall_score": round(score, 4), "decision_threshold": threshold,
                "window_packets": len(recs),
                "window_start": recs[0].timestamp.isoformat() if recs[0].timestamp else None,
                "window_end": recs[-1].timestamp.isoformat() if recs[-1].timestamp else None,
                "noise_floor_median": (float(np.median([r.noise_floor for r in recs if r.noise_floor is not None]))
                                       if any(r.noise_floor is not None for r in recs) else None),
                "snr_db": q["snr_db"], "completeness": q["completeness"],
                "score_note": "uncalibrated heuristic; not the probability that a fall happened",
                "features": {n: round(float(v), 5) for n, v in zip(names, vec)},
            },
            inferred_activity_id=act.id, model_confidence=float(confidence), source=device.allowed_source,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        _mark(session, recs, event.id)

        alert = _raise_possible_fall(session, device, event, score, q["quality"]) if suspected else None
        result["detections"].append({
            "event_id": event.id, "activity": act.name, "fall_suspected": bool(suspected),
            "fall_score": round(score, 4), "confidence": round(float(confidence), 4),
            "signal_quality": q["quality"], "window_packets": len(recs), "source": device.allowed_source,
            "alert_id": alert.id if alert else None,
        })
    return result
