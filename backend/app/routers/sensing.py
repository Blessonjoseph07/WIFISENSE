from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime
from typing import Dict, Any, List
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import SensingDevice, Room, Floor, Building, SensingEvent, ActivityType, Alert, RoomCalibration
from app.schemas.schemas import SensingEventSimulate
from app.services.notifications import process_alert_notifications

router = APIRouter(prefix="/sensing", tags=["Sensing Pipeline"])
STAFF_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver", "corporate_staff"]

DETERMINISTIC_PROFILES = {
    "Empty": {
        "rssi": -52,
        "subcarriers": 56,
        "signal_quality": 95,
        "confidence": 0.98,
        "event_type": "PresenceEnded",
        "features": {"variance_amplitude": 0.021, "entropy_phase": 0.082, "doppler_shift_hz": 0.0}
    },
    "Presence": {
        "rssi": -48,
        "subcarriers": 56,
        "signal_quality": 94,
        "confidence": 0.94,
        "event_type": "PresenceStarted",
        "features": {"variance_amplitude": 0.285, "entropy_phase": 0.312, "doppler_shift_hz": 0.8}
    },
    "Walking": {
        "rssi": -45,
        "subcarriers": 56,
        "signal_quality": 93,
        "confidence": 0.91,
        "event_type": "MotionDetected",
        "features": {"variance_amplitude": 1.152, "entropy_phase": 0.745, "doppler_shift_hz": 2.6}
    },
    "Sitting": {
        "rssi": -47,
        "subcarriers": 56,
        "signal_quality": 96,
        "confidence": 0.95,
        "event_type": "MotionSettled",
        "features": {"variance_amplitude": 0.124, "entropy_phase": 0.198, "doppler_shift_hz": 0.3}
    },
    "Fall_Detected": {
        "rssi": -42,
        "subcarriers": 56,
        "signal_quality": 92,
        "confidence": 0.97,
        "event_type": "FallDetected",
        "features": {"variance_amplitude": 2.450, "entropy_phase": 0.892, "doppler_shift_hz": 4.8}
    },
    "Resting": {
        "rssi": -49,
        "subcarriers": 56,
        "signal_quality": 95,
        "confidence": 0.96,
        "event_type": "MotionSettled",
        "features": {"variance_amplitude": 0.065, "entropy_phase": 0.145, "doppler_shift_hz": 0.1}
    }
}

ACTIVITY_MAPPING = {
    "Empty": (1, "STATUS"),
    "Presence": (2, "STATUS"),
    "Walking": (3, "ACTIVITY"),
    "Sitting": (4, "ACTIVITY"),
    "Fall_Detected": (5, "CRITICAL"),
    "Resting": (6, "ACTIVITY")
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
    background_tasks: BackgroundTasks,
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
        bld = session.get(Building, flr.building_id) if flr else None
        if bld and (bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"] and room.id not in scopes["room_ids"]):
            raise HTTPException(status_code=403, detail="Not authorized to simulate events for this room.")

    device.device_status = "ONLINE"
    device.last_seen_at = datetime.utcnow()
    session.add(device)

    activity_name = event_data.simulated_activity
    if activity_name not in ACTIVITY_MAPPING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid simulated activity name. Allowed: {list(ACTIVITY_MAPPING.keys())}")

    activity_id, category = ACTIVITY_MAPPING[activity_name]
    profile = DETERMINISTIC_PROFILES.get(activity_name, DETERMINISTIC_PROFILES["Presence"])

    sensing_event = SensingEvent(
        device_id=device.id,
        room_id=room.id,
        timestamp=datetime.utcnow(),
        rssi=profile["rssi"],
        subcarrier_count=profile["subcarriers"],
        signal_quality=profile["signal_quality"],
        event_type=profile["event_type"],
        raw_csi_payload_path=None,
        extracted_features=profile["features"],
        inferred_activity_id=activity_id,
        model_confidence=profile["confidence"]
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
        
        background_tasks.add_task(
            process_alert_notifications,
            alert_id=db_alert.id,
            room_id=room.id,
            alert_msg=alert_msg
        )

        notification_details = {
            "channel": "dashboard_ws_push",
            "recipient_role": "caregiver",
            "message": alert_msg,
            "timestamp": datetime.utcnow().strftime("%d %b %Y %H:%M:%S"),
            "status": "SENT"
        }

    return {
        "message": "Deterministic CSI sensing event simulated successfully (RuView-inspired telemetry format).",
        "presence_detected": presence_detected,
        "activity_classified": activity_name,
        "alert_triggered": alert_triggered,
        "sensing_event": {
            "id": sensing_event.id,
            "device_id": sensing_event.device_id,
            "room_id": sensing_event.room_id,
            "timestamp": sensing_event.timestamp.isoformat(),
            "rssi": sensing_event.rssi,
            "subcarrier_count": sensing_event.subcarrier_count,
            "signal_quality": sensing_event.signal_quality,
            "event_type": sensing_event.event_type,
            "extracted_features": sensing_event.extracted_features,
            "confidence": float(sensing_event.model_confidence)
        },
        "alert": {
            "id": db_alert.id,
            "room_name": room.name,
            "severity": db_alert.severity,
            "status": db_alert.status,
            "message": db_alert.message,
            "created_at": db_alert.created_at.strftime("%d %b %Y %H:%M:%S")
        } if db_alert else None,
        "notification": notification_details
    }

@router.get("/devices/{device_id}/csi-telemetry", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_device_csi_telemetry(
    device_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    device = session.get(SensingDevice, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")

    latest_event = session.exec(
        select(SensingEvent).where(SensingEvent.device_id == device_id).order_by(SensingEvent.timestamp.desc())
    ).first()

    room = session.get(Room, device.room_id) if device.room_id else None
    cal = session.exec(select(RoomCalibration).where(RoomCalibration.room_id == device.room_id)).first() if room else None

    # Deterministic subcarrier spectrum generation for visualization (RuView reference: 56 subcarriers)
    subcarriers_data = []
    base_amp = 1.0 if not latest_event else (1.4 if latest_event.extracted_features.get("doppler_shift_hz", 0) > 1.0 else 0.8)
    for i in range(56):
        # Deterministic wave shape
        amp = round(base_amp + 0.15 * ((i % 7) - 3) / 3.0, 3)
        phase = round(-3.14 + (6.28 * i / 55), 2)
        subcarriers_data.append({"subcarrier_index": i, "amplitude": amp, "phase_rad": phase})

    signal_quality = latest_event.signal_quality if (latest_event and latest_event.signal_quality) else 94
    recommendation = "Normal operating parameters." if signal_quality >= 75 else "SIGNAL QUALITY LOW. Check sensor placement or interference."

    return {
        "device_id": device.id,
        "mac_address": device.mac_address,
        "room_name": room.name if room else "Unassigned",
        "signal_quality_pct": signal_quality,
        "subcarrier_count": 56,
        "rssi_dbm": latest_event.rssi if latest_event else -47,
        "baseline_calibration": {
            "status": cal.baseline_status if cal else "VALID",
            "rf_similarity_pct": cal.rf_similarity_pct if cal else 96.0,
            "environment_status": cal.rf_environment_status if cal else "NORMAL",
            "captured_at": cal.baseline_captured_at.strftime("%H:%M:%S") if cal else "07:00:00"
        },
        "motion_energy": latest_event.extracted_features.get("variance_amplitude", 0.12) if latest_event else 0.12,
        "doppler_shift_hz": latest_event.extracted_features.get("doppler_shift_hz", 0.0) if latest_event else 0.0,
        "confidence_pct": round((latest_event.model_confidence if latest_event else 0.94) * 100, 1),
        "activity_detected": "Resting" if not latest_event else session.get(ActivityType, latest_event.inferred_activity_id).name,
        "recommendation": recommendation,
        "spectrum": subcarriers_data,
        "note": "CSI sensing telemetry generated via deterministic OFDM RF simulation model."
    }

