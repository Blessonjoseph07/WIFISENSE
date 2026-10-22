"""
DATASET REPLAY evaluation.

Replayed recordings come with ground-truth labels. They are NEVER sent in packets (the ingest endpoint rejects label
keys). An administrator-run replay tool records the label here, separately, after the detector has produced its own
result for that window, so the two can be compared honestly.

The summary reports how the detector did on REPLAYED, RECORDED data. It says nothing about live accuracy.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.audit import record_audit_event
from app.core.database import get_session
from app.models.entities import ActivityType, ReplayEvaluation, SensingEvent
from app.routers.auth import get_current_user, require_roles
from app.routers.sensing import STAFF_ROLES, user_can_access_room
from app.schemas.schemas import ReplayEvaluationCreate

router = APIRouter(prefix="/sensing/replay", tags=["Dataset Replay"])

WRITE_ROLES = ["system_admin", "facility_manager"]
POSITIVE_LABEL = "fall"


@router.post("/evaluations", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(WRITE_ROLES))])
def record_ground_truth(
    body: ReplayEvaluationCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    event = session.get(SensingEvent, body.event_id)
    if not event or not user_can_access_room(current_user, event.room_id, session):
        raise HTTPException(status_code=404, detail="Detection event not found.")  # same answer for missing / not yours
    if event.source != "dataset":
        raise HTTPException(status_code=400, detail="Ground truth can only be attached to DATASET REPLAY events.")
    if session.exec(select(ReplayEvaluation).where(ReplayEvaluation.event_id == event.id)).first():
        raise HTTPException(status_code=409, detail="This detection already has a recorded label.")
    row = ReplayEvaluation(event_id=event.id, device_id=event.device_id, dataset_name=body.dataset_name.strip(),
                           recorded_label=body.recorded_label.strip(), created_by=current_user.id)
    session.add(row)
    session.commit()
    record_audit_event(session=session, what_action="REPLAY_LABEL_RECORDED", resource_type="SENSING_EVENT",
                       resource_id=str(event.id), who_user_id=current_user.id, who_email=current_user.email,
                       details={"dataset": row.dataset_name})
    return {"event_id": event.id, "recorded_label": row.recorded_label, "dataset_name": row.dataset_name}


@router.get("/summary", dependencies=[Depends(require_roles(STAFF_ROLES))])
def replay_summary(
    device_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(ReplayEvaluation, SensingEvent, ActivityType)
        .join(SensingEvent, SensingEvent.id == ReplayEvaluation.event_id)
        .join(ActivityType, ActivityType.id == SensingEvent.inferred_activity_id)
    )
    if device_id:
        stmt = stmt.where(ReplayEvaluation.device_id == device_id)
    visible: Dict[str, bool] = {}
    tp = fn = fp = tn = 0
    by_label: Dict[str, Dict[str, int]] = {}
    by_dataset: Dict[str, Dict[str, int]] = {}
    for ev_eval, event, act in session.exec(stmt).all():
        if event.room_id not in visible:
            visible[event.room_id] = user_can_access_room(current_user, event.room_id, session)
        if not visible[event.room_id]:
            continue
        actual_fall = ev_eval.recorded_label.strip().lower() == POSITIVE_LABEL
        flagged = act.name == "Possible_Fall"
        tp += actual_fall and flagged
        fn += actual_fall and not flagged
        fp += (not actual_fall) and flagged
        tn += (not actual_fall) and not flagged
        row = by_label.setdefault(ev_eval.recorded_label, {"windows": 0, "flagged_possible_fall": 0})
        row["windows"] += 1
        row["flagged_possible_fall"] += int(flagged)
        ds = by_dataset.setdefault(ev_eval.dataset_name, {"windows": 0, "recorded_falls": 0, "falls_flagged": 0,
                                                          "non_falls": 0, "non_falls_flagged": 0})
        ds["windows"] += 1
        ds["recorded_falls" if actual_fall else "non_falls"] += 1
        ds["falls_flagged" if actual_fall and flagged else "non_falls_flagged"] += int(flagged)
    n = tp + fn + fp + tn
    recall = tp / (tp + fn) if (tp + fn) else None
    fpr = fp / (fp + tn) if (fp + tn) else None
    out: Dict[str, Any] = {
        "windows_evaluated": n,
        "recorded_fall_windows": tp + fn,
        "recorded_non_fall_windows": fp + tn,
        "possible_fall_flagged_on_recorded_falls": tp,
        "missed_recorded_falls": fn,
        "false_alarms_on_recorded_non_falls": fp,
        "correct_non_falls": tn,
        "fall_recall": round(recall, 3) if recall is not None else None,
        "false_alarm_rate": round(fpr, 3) if fpr is not None else None,
        "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
        "by_recorded_label": by_label,
        "by_dataset": by_dataset,
        "statement": ("Result of REPLAYED, RECORDED data compared with the labels that came with the dataset. "
                      "It describes this model on that dataset, not accuracy on live hardware."),
    }
    return out
