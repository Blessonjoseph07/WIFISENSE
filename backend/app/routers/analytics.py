from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.routers.auth import get_current_user
from app.models.entities import Room, SensingEvent, ActivityType, Alert
from app.schemas.schemas import OccupancySummaryOut, AlertSummaryOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/occupancy-summary", response_model=OccupancySummaryOut)
def get_occupancy_summary(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    rooms = session.exec(select(Room)).all()
    total_rooms = len(rooms)
    occupied_rooms = 0
    vacant_rooms = 0
    occupied_room_details = []

    for r in rooms:
        # Query the latest sensing event for the room to check its status
        stmt = select(SensingEvent).where(SensingEvent.room_id == r.id).order_by(SensingEvent.timestamp.desc())
        latest_event = session.exec(stmt).first()
        
        is_occupied = False
        activity = "Empty"
        confidence = 0.0
        last_update = None

        if latest_event:
            # Look up inferred activity name
            act_type = session.get(ActivityType, latest_event.inferred_activity_id)
            if act_type:
                activity = act_type.name
                if activity != "Empty":
                    is_occupied = True
            confidence = float(latest_event.model_confidence)
            last_update = latest_event.timestamp.isoformat()

        if is_occupied:
            occupied_rooms += 1
        else:
            vacant_rooms += 1

        occupied_room_details.append({
            "room_id": r.id,
            "room_name": r.name,
            "room_type": r.room_type,
            "is_occupied": is_occupied,
            "current_activity": activity,
            "model_confidence": confidence,
            "last_updated": last_update
        })

    rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0.0
    return OccupancySummaryOut(
        total_rooms=total_rooms,
        occupied_rooms=occupied_rooms,
        vacant_rooms=vacant_rooms,
        occupancy_rate=round(rate, 2),
        occupied_room_details=occupied_room_details
    )

@router.get("/alert-summary", response_model=AlertSummaryOut)
def get_alert_summary(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    alerts = session.exec(select(Alert)).all()
    total_alerts = len(alerts)

    status_counts = {"new": 0, "acknowledged": 0, "resolved": 0}
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for a in alerts:
        # Increment status counts
        if a.status in status_counts:
            status_counts[a.status] += 1
        else:
            status_counts[a.status] = 1

        # Increment severity counts
        if a.severity in severity_counts:
            severity_counts[a.severity] += 1
        else:
            severity_counts[a.severity] = 1

    return AlertSummaryOut(
        total_alerts=total_alerts,
        status_counts=status_counts,
        severity_counts=severity_counts
    )
