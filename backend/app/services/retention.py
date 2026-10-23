"""
Rolling retention for raw CSI packets.

Raw packets are evidence for the detector, not a long-term record: once a window has been analysed (or skipped) the
detection result in sensing_events is what the product keeps. This module deletes analysed packets that are older than
the retention window, and, as a hard safety limit, the oldest analysed packets once the table passes a row cap.

Packets the detector has not processed yet (event_id IS NULL) are never deleted by the age rule, so a slow or stopped
detector cannot lose data. If the table is still over the cap with nothing analysed left to delete, the status says so
instead of silently dropping unprocessed packets.
"""
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import delete, func
from sqlmodel import Session, select

from app.core.config import settings
from app.models.entities import RawCsiTelemetry

BATCH = 5000

_state_lock = threading.Lock()
_last_run: Dict[str, Any] = {"at": None, "deleted_by_age": 0, "deleted_by_cap": 0, "error": None}


def _delete_ids(session: Session, ids) -> int:
    if not ids:
        return 0
    session.exec(delete(RawCsiTelemetry).where(RawCsiTelemetry.id.in_(ids)))
    session.commit()
    return len(ids)


def prune_raw_csi(session: Session, retention_hours: Optional[float] = None, max_rows: Optional[int] = None,
                  now: Optional[datetime] = None) -> Dict[str, int]:
    """Apply the retention rules once. Returns how many packets each rule deleted."""
    hours = settings.RAW_CSI_RETENTION_HOURS if retention_hours is None else retention_hours
    cap = settings.RAW_CSI_MAX_ROWS if max_rows is None else max_rows
    now = now or datetime.now(timezone.utc)
    by_age = by_cap = 0

    if hours and hours > 0:
        cutoff = now - timedelta(hours=hours)
        while True:
            ids = session.exec(
                select(RawCsiTelemetry.id)
                .where(RawCsiTelemetry.created_at < cutoff, RawCsiTelemetry.event_id.is_not(None))
                .order_by(RawCsiTelemetry.id).limit(BATCH)
            ).all()
            if not ids:
                break
            by_age += _delete_ids(session, ids)

    if cap and cap > 0:
        while True:
            total = session.exec(select(func.count()).select_from(RawCsiTelemetry)).one()
            excess = total - cap
            if excess <= 0:
                break
            ids = session.exec(
                select(RawCsiTelemetry.id).where(RawCsiTelemetry.event_id.is_not(None))
                .order_by(RawCsiTelemetry.id).limit(min(BATCH, excess))
            ).all()
            if not ids:  # only unprocessed packets are left: never drop those silently
                break
            by_cap += _delete_ids(session, ids)

    with _state_lock:
        _last_run.update(at=now.isoformat(), deleted_by_age=by_age, deleted_by_cap=by_cap, error=None)
    return {"deleted_by_age": by_age, "deleted_by_cap": by_cap}


def retention_status(session: Session, max_rows: Optional[int] = None) -> Dict[str, Any]:
    total = session.exec(select(func.count()).select_from(RawCsiTelemetry)).one()
    pending = session.exec(select(func.count()).select_from(RawCsiTelemetry).where(RawCsiTelemetry.event_id.is_(None))).one()
    oldest = session.exec(select(func.min(RawCsiTelemetry.created_at))).one()
    cap = settings.RAW_CSI_MAX_ROWS if max_rows is None else max_rows
    with _state_lock:
        last = dict(_last_run)
    return {
        "policy": {
            "retention_hours": settings.RAW_CSI_RETENTION_HOURS,
            "max_rows": cap,
            "prune_interval_seconds": settings.RAW_CSI_PRUNE_INTERVAL_SECONDS,
            "scope": "raw CSI packets only; detections, alerts and audit history are kept",
            "unprocessed_packets_are_never_age_deleted": True,
        },
        "raw_packets_stored": total,
        "raw_packets_unprocessed": pending,
        "oldest_raw_packet_at": oldest.isoformat() if oldest else None,
        "cap_used_fraction": round(total / cap, 3) if cap else None,
        "over_cap_with_nothing_deletable": bool(cap and total > cap and total - pending <= 0),
        "last_prune": last,
    }


def start_background_pruner(engine) -> Optional[threading.Thread]:
    """One daemon thread per process. Safe with several instances: the delete is idempotent."""
    interval = settings.RAW_CSI_PRUNE_INTERVAL_SECONDS
    if interval <= 0:
        return None

    def loop():
        while True:
            time.sleep(interval)
            try:
                with Session(engine) as session:
                    prune_raw_csi(session)
            except Exception as exc:  # noqa: BLE001 - never let the pruner thread die
                with _state_lock:
                    _last_run["error"] = f"{type(exc).__name__}: {exc}"[:200]

    t = threading.Thread(target=loop, name="raw-csi-pruner", daemon=True)
    t.start()
    return t
