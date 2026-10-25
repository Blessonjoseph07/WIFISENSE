"""
Phase 2: learn this room. Record short labelled segments, train a small classifier on them, estimate the room state live.
See app/services/occupancy.py for exactly what it is and is not.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.audit import record_audit_event
from app.core.database import get_session
from app.models.entities import RawCsiTelemetry, RoomCalibration, SensingDevice
from app.routers.auth import get_current_user, require_roles
from app.routers.sensing import (STAFF_ROLES, STALE_SECONDS, _calibration, _human_duration, _movement_device, _recent_records,
                                 _seconds_since, get_authenticated_device, movement_snapshot)
from app.services import movement, occupancy

router = APIRouter(prefix="/sensing", tags=["Occupancy (Phase 2)"])
MANAGER_ROLES = ["system_admin", "facility_manager"]

CAVEATS = [
    "This estimates a room state (empty, someone still, someone walking, or a crowd level) from one pair of boards. It does not count, locate or identify people.",
    "It learned only from what you recorded, at this board placement. If the room or the boards move, record again.",
    "The held-out accuracy is measured on part of the same recordings; real-world accuracy can be lower. Re-check it on a different day.",
]


class CaptureIn(BaseModel):
    label: Literal["empty", "still", "walking", "few", "busy"]
    seconds: int = Field(30, ge=5, le=180)
    # Optional: use the packets stored since this packet id (see latest_id in the live endpoint) instead of "the last N seconds".
    from_packet_id: Optional[int] = Field(default=None, ge=0)


def _state(session: Session, device_id: str) -> Dict[str, Any]:
    cal = _calibration(session, device_id)
    return dict(((cal.subcarrier_profile or {}).get("occupancy") or {}) if cal else {})


def _save(session: Session, device, occ: Dict[str, Any]) -> None:
    cal = _calibration(session, device.id)
    profile = dict((cal.subcarrier_profile or {}) if cal else {})
    if occ:
        profile["occupancy"] = occ
    else:
        profile.pop("occupancy", None)
    if cal:
        cal.subcarrier_profile = profile
        cal.updated_at = datetime.now(timezone.utc)
        session.add(cal)
    else:
        session.add(RoomCalibration(room_id=device.room_id, device_id=device.id, subcarrier_profile=profile))
    session.commit()
    with movement._cache_lock:
        movement._cache.pop(f"occ:{device.id}", None)


def _summary(occ: Dict[str, Any]) -> Dict[str, Any]:
    sessions = occ.get("sessions") or {}
    return {l: {"sessions": len(sessions.get(l, [])), "blocks": sum(len(occupancy.compatible(s["blocks"])) for s in sessions.get(l, []))}
            for l in occupancy.LABELS}


def room_state_snapshot(session: Session, device_id: str, model: Dict[str, Any]) -> Dict[str, Any]:
    """The learned model's estimate from the device's latest packets (cached ~1.5 s)."""
    def build():
        recs = _recent_records(session, device_id, occupancy.PREDICT_BLOCKS * occupancy.BLOCK)
        idle = _seconds_since(recs[-1].created_at) if recs else None
        if not recs or idle is None or idle > STALE_SECONDS:
            return {"state": "NOT_SENDING", "prediction": None,
                    "detail": f"The last packet arrived {_human_duration(idle)} ago." if idle is not None else "No packets yet."}
        feats = occupancy.block_features(recs)
        if len(feats) < 3:
            return {"state": "NOT_ENOUGH_DATA", "prediction": None, "detail": "Waiting for a few seconds of readings."}
        return {"state": "READY", "prediction": occupancy.predict(model, feats), "detail": None}
    return movement.cached(f"occ:{device_id}", build)


MOTIONLESS = ("empty", "still")
MOVING = ("walking", "few", "busy")
PRESENCE_WINDOW_BLOCKS = 10    # about the last 10 seconds


def presence_from_movement(mv: Dict[str, Any]) -> Dict[str, Any]:
    """'Presence detected' with a measured confidence: the share of the last ~10 one-second blocks in which the signal was
    above the empty-room threshold. It is a count, not a model probability, so it is always marked reliable."""
    blocks, thr = (mv.get("blocks") or [])[-PRESENCE_WINDOW_BLOCKS:], mv.get("threshold")
    share = (sum(1 for b in blocks if thr is not None and b > thr) / len(blocks)) if blocks else 0.0
    return {"label": "presence", "text": "Presence detected", "confidence": round(share, 2), "reliable": True,
            "source": "movement", "detail": f"{sum(1 for b in blocks if thr is not None and b > thr)} of the last {len(blocks)} seconds above the empty-room level"}


def reconcile(pred: Optional[Dict[str, Any]], mv: Dict[str, Any], reliable: bool):
    """What the board shows, given the model's answer and the movement check, and why (None when they agree).

    The movement check measures fluctuation directly against this room's empty level, so it has the last word on MOVING
    versus NOT MOVING; the model only chooses within that:
      * clear movement but a motionless answer (usually: walking never recorded) -> 'Presence detected' with the measured share;
      * a moving answer without movement (the model can also latch onto signal strength: a person standing in the radio
        path lowers it much like walking did) -> the model's best motionless answer, renormalised over those situations."""
    if not pred:
        return None, None
    shown = {"label": pred["label"], "text": pred["text"], "confidence": pred["confidence"], "reliable": reliable}
    moving_now = mv.get("state") == "MOVEMENT"
    if moving_now and pred["label"] in MOTIONLESS:
        return presence_from_movement(mv), (f"The movement check sees clear movement, so the board shows Presence detected "
                                            f"instead of \"{pred['text']}\".")
    if not moving_now and pred["label"] in MOVING:
        probs = {l: p for l, p in (pred.get("probabilities") or {}).items() if l in MOTIONLESS}
        if probs and sum(probs.values()) > 0:
            best = max(probs, key=probs.get)
            shown = {"label": best, "text": occupancy.LABEL_TEXT[best], "confidence": round(probs[best] / sum(probs.values()), 3),
                     "reliable": reliable}
        else:
            shown = presence_from_movement(mv)
        return shown, (f"No movement above the empty-room level, so the board does not show \"{pred['text']}\" "
                       f"and shows \"{shown['text']}\" instead.")
    return shown, None


@router.get("/device/state")
def get_own_state(device: SensingDevice = Depends(get_authenticated_device), session: Session = Depends(get_session)):
    """What the board itself may show on its display: presence from the empty-room reference and, once a model has been trained in
    this room, its estimate. Authenticated with the device's own token, like /sensing/ingest; returns nothing about people or rooms."""
    mv = movement_snapshot(session, device.id)
    stored = _state(session, device.id).get("model")
    model = stored if occupancy.model_compatible(stored) else None
    room = None
    if model:
        res = room_state_snapshot(session, device.id, model)
        pred = res.get("prediction")
        if pred:
            ev = _state(session, device.id).get("evaluation") or {}
            room, _ = reconcile(pred, mv, bool(ev.get("reliable")))
    return {"presence": mv["presence"], "movement_state": mv["state"], "headline": mv["headline"],
            "seconds_since_last_packet": mv["seconds_since_last_packet"], "room_state": room}


@router.get("/devices/{device_id}/occupancy", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_occupancy(device_id: str, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    device = _movement_device(device_id, session, current_user)
    occ = _state(session, device_id)
    stored = occ.get("model")
    model = stored if occupancy.model_compatible(stored) else None      # a model from an older feature set must be retrained
    samples = _summary(occ)
    out: Dict[str, Any] = {
        "device_id": device.id,
        "mode": {"simulated": "DEMO", "dataset": "DATASET REPLAY", "live": "LIVE HARDWARE"}.get(device.allowed_source or "live", "LIVE HARDWARE"),
        "labels": [{"id": l, "text": occupancy.LABEL_TEXT[l]} for l in occupancy.LABELS],
        "samples": samples,
        "can_train": sum(1 for v in samples.values() if v["blocks"] >= occupancy.MIN_BLOCKS_PER_LABEL) >= 2,
        "min_blocks_per_label": occupancy.MIN_BLOCKS_PER_LABEL,
        "block_packets": occupancy.BLOCK,
        "trained": bool(model),
        "evaluation": occ.get("evaluation") if model else None,
        "retrain_needed": bool(stored) and not model,
        "caveats": CAVEATS,
        "prediction": None,
        "prediction_state": "NO_MODEL" if not model else "READY",
    }
    if model:
        res = room_state_snapshot(session, device_id, model)
        out["prediction"], out["prediction_state"], out["prediction_detail"] = res["prediction"], res["state"], res["detail"]
        _, out["override_reason"] = reconcile(res["prediction"], movement_snapshot(session, device_id),
                                              bool((occ.get("evaluation") or {}).get("reliable")))
    return out


@router.post("/devices/{device_id}/occupancy/capture", dependencies=[Depends(require_roles(MANAGER_ROLES))])
def capture_occupancy(device_id: str, body: CaptureIn, request: Request, session: Session = Depends(get_session),
                      current_user=Depends(get_current_user)):
    """Save the LAST `seconds` seconds of this device's packets as an example of `label`. Call it when the segment is over."""
    device = _movement_device(device_id, session, current_user)
    stmt = select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id)
    if body.from_packet_id is not None:
        stmt = stmt.where(RawCsiTelemetry.id >= body.from_packet_id)
    else:
        stmt = stmt.where(RawCsiTelemetry.created_at >= datetime.now(timezone.utc) - timedelta(seconds=body.seconds))
    recs = session.exec(stmt.order_by(RawCsiTelemetry.id).limit(180 * 130 + 200)).all()
    idle = _seconds_since(recs[-1].created_at) if recs else None
    if not recs or idle is None or idle > 15:
        raise HTTPException(status_code=409, detail="The board is not sending right now, so there is nothing to record.")
    feats = occupancy.block_features(recs)
    if len(feats) < 8:
        raise HTTPException(status_code=409, detail=f"Only {len(recs)} packets arrived in the last {body.seconds} s (need about "
                                                    f"{8 * occupancy.BLOCK}). Check the board is sending steadily and try again.")
    occ = _state(session, device_id)
    sessions = {l: list(v) for l, v in (occ.get("sessions") or {}).items()}
    lst = sessions.setdefault(body.label, [])
    lst.append({"captured_at": datetime.now(timezone.utc).isoformat(), "seconds": body.seconds, "packets": len(recs),
                "blocks": [[round(x, 5) for x in f] for f in feats]})
    sessions[body.label] = lst[-occupancy.MAX_SESSIONS_PER_LABEL:]
    occ["sessions"] = sessions
    occ.pop("model", None)            # the old model no longer matches the data: train again
    occ.pop("evaluation", None)
    _save(session, device, occ)
    record_audit_event(session=session, what_action="OCCUPANCY_SEGMENT_RECORDED", resource_type="DEVICE", resource_id=device.id,
                       who_user_id=current_user.id, who_email=current_user.email,
                       details={"label": body.label, "seconds": body.seconds, "blocks": len(feats)}, request=request)
    return {"label": body.label, "blocks_saved": len(feats), "packets": len(recs), "samples": _summary(occ)}


@router.post("/devices/{device_id}/occupancy/train", dependencies=[Depends(require_roles(MANAGER_ROLES))])
def train_occupancy(device_id: str, request: Request, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    device = _movement_device(device_id, session, current_user)
    occ = _state(session, device_id)
    try:
        result = occupancy.train(occ.get("sessions") or {})
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    occ["model"], occ["evaluation"] = result["model"], result["evaluation"]
    _save(session, device, occ)
    ev = result["evaluation"]
    record_audit_event(session=session, what_action="OCCUPANCY_MODEL_TRAINED", resource_type="DEVICE", resource_id=device.id,
                       who_user_id=current_user.id, who_email=current_user.email,
                       details={"heldout_accuracy": ev["heldout_accuracy"], "reliable": ev["reliable"], "labels": result["model"]["labels"]}, request=request)
    return {"evaluation": ev}


@router.delete("/devices/{device_id}/occupancy", dependencies=[Depends(require_roles(MANAGER_ROLES))])
def reset_occupancy(device_id: str, request: Request, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    device = _movement_device(device_id, session, current_user)
    _save(session, device, {})
    record_audit_event(session=session, what_action="OCCUPANCY_RESET", resource_type="DEVICE", resource_id=device.id,
                       who_user_id=current_user.id, who_email=current_user.email, request=request)
    return {"reset": True}
