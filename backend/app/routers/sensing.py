from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import random
from datetime import datetime
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import SensingDevice, Room, Floor, Building, SensingEvent, ActivityType, Alert
from app.schemas.schemas import SensingEventSimulate

router = APIRouter(prefix="/sensing", tags=["Sensing Pipeline"])
STAFF_ROLES = ["system_admin", "organization_admin", "facility_manager", "corporate_staff"]

ACTIVITY_MAPPING = {
    "Empty": (1, "STATUS"),
    "Presence": (2, "STATUS"),
    "Walking": (3, "ACTIVITY"),
    "Sitting": (4, "ACTIVITY"),
    "Fall_Detected": (5, "CRITICAL")
}

def seed_activity_types_if_empty(session: Session):
    for name, (act_id, category) in ACTIVITY_MAPPING.items():
        existing = session.get(ActivityType, act_id)
        if not existing:
            new_act = ActivityType(id=act_id, name=name, category=category)
            session.add(new_act)
    session.commit()

@router.post("/simulate-event", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(STAFF_ROLES))])
def simulate_event(
    event_data: SensingEventSimulate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    seed_activity_types_if_empty(session)

    device = session.get(SensingDevice, event_data.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered sensing device not found.")

    if not device.room_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The device must be registered to a room before simulating events.")

    room = session.get(Room, device.room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room assigned to device does not exist.")

    # Scoping check
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"]:
        flr = session.get(Floor, room.floor_id)
        bld = session.get(Building, flr.building_id)
        if bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"] and room.id not in scopes["room_ids"]:
            raise HTTPException(status_code=403, detail="Not authorized to simulate events for this room.")

    device.device_status = "ONLINE"
    device.last_seen_at = datetime.utcnow()
    session.add(device)
    session.commit()

    activity_name = event_data.simulated_activity
    if activity_name not in ACTIVITY_MAPPING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid simulated activity name. Allowed: {list(ACTIVITY_MAPPING.keys())}")

    activity_id, category = ACTIVITY_MAPPING[activity_name]

    rssi_val = random.randint(-65, -35)
    confidence = round(random.uniform(0.85, 0.99), 4)
    mock_features = {
        "variance_amplitude": round(random.uniform(0.05, 1.8), 4),
        "entropy_phase": round(random.uniform(0.1, 0.8), 4),
        "doppler_shift_hz": round(random.uniform(0.0, 5.0), 2)
    }

    sensing_event = SensingEvent(
        device_id=device.id,
        room_id=room.id,
        timestamp=datetime.utcnow(),
        rssi=rssi_val,
        subcarrier_count=64,
        raw_csi_payload_path=None,
        extracted_features=mock_features,
        inferred_activity_id=activity_id,
        model_confidence=confidence
    )
    session.add(sensing_event)
    session.commit()
    session.refresh(sensing_event)

    presence_detected = (activity_name != "Empty")
    alert_triggered = False
    db_alert = None
    notification_details = None

    if activity_name == "Fall_Detected":
        alert_triggered = True
        alert_msg = f"Critical Fall Detected in Room {room.name}!"
        db_alert = Alert(
            room_id=room.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message=alert_msg,
            status="new"
        )
        session.add(db_alert)
        session.commit()
        session.refresh(db_alert)

        notification_details = {
            "channel": "dashboard_ws_push",
            "recipient_role": "caregiver",
            "message": alert_msg,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "SENT"
        }

    return {
        "message": "CSI sensing event simulation pipeline executed successfully.",
        "presence_detected": presence_detected,
        "activity_classified": activity_name,
        "alert_triggered": alert_triggered,
        "sensing_event": {
            "id": sensing_event.id,
            "device_id": sensing_event.device_id,
            "room_id": sensing_event.room_id,
            "timestamp": sensing_event.timestamp.isoformat(),
            "rssi": sensing_event.rssi,
            "extracted_features": sensing_event.extracted_features,
            "confidence": float(sensing_event.model_confidence)
        },
        "alert": {
            "id": db_alert.id,
            "room_name": room.name,
            "severity": db_alert.severity,
            "status": db_alert.status,
            "message": db_alert.message,
            "created_at": db_alert.created_at.isoformat()
        } if db_alert else None,
        "notification": notification_details
    }
