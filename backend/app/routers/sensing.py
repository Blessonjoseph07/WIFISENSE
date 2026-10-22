import secrets
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header, Request, Query
from sqlmodel import Session, select, or_, func
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from app.core.database import get_session
from app.core.security import hash_token
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import SensingDevice, Room, Floor, Building, SensingEvent, ActivityType, Alert, RoomCalibration, RawCsiTelemetry, ReplayEvaluation
from app.schemas.schemas import SensingEventSimulate, CsiPacketIn, CsiIngestBatch, CsiIngestOut, SensingHistoryOut
from app.core.confidence import confidence_level, signal_level, requires_verification
from app.services.notifications import process_alert_notifications
from app.services import detection, fall_model

router = APIRouter(prefix="/sensing", tags=["Sensing Pipeline"])
STAFF_ROLES = ["system_admin", "facility_manager", "caregiver", "corporate_staff"]
MAX_INGEST_PAYLOAD_BYTES = 64 * 1024  # 64 KB maximum request/payload limit
# A device an admin has pulled for repair must not flip itself back to ONLINE by sending packets.
# OFFLINE is deliberately allowed: a newly registered device starts OFFLINE and becomes ONLINE on first packet.
INGEST_BLOCKED_STATUSES = {"FAULT_REPORTED", "INSPECTING", "SERVICING"}

async def verify_ingest_payload_size(request: Request):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_INGEST_PAYLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Payload size ({content_length} bytes) exceeds maximum allowed limit of {MAX_INGEST_PAYLOAD_BYTES // 1024} KB."
                )
        except ValueError:
            pass

    body = await request.body()
    if len(body) > MAX_INGEST_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload size ({len(body)} bytes) exceeds maximum allowed limit of {MAX_INGEST_PAYLOAD_BYTES // 1024} KB."
        )

def get_authenticated_device(
    x_device_token: Optional[str] = Header(None, alias="X-Device-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    session: Session = Depends(get_session)
) -> SensingDevice:
    raw_token = None
    if x_device_token:
        raw_token = x_device_token.strip()
    elif authorization and authorization.startswith("Bearer "):
        raw_token = authorization[7:].strip()
    
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing device authentication token. Provide X-Device-Token or Bearer token."
        )
    
    incoming_hash = hash_token(raw_token)
    device = session.exec(
        select(SensingDevice).where(SensingDevice.hardware_token_hash == incoming_hash)
    ).first()

    if not device or not secrets.compare_digest(device.hardware_token_hash or "", incoming_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device authentication token."
        )

    if not device.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device '{device.id}' ({device.mac_address}) is not assigned to a room. Telemetry rejected."
        )

    room = session.get(Room, device.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room '{device.room_id}' assigned to device does not exist."
        )

    if device.device_status in INGEST_BLOCKED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device '{device.id}' is {device.device_status} and may not ingest telemetry until an administrator returns it to service."
        )

    return device

@router.post(
    "/ingest",
    response_model=CsiIngestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_ingest_payload_size)],
    summary="Ingest Raw CSI Telemetry Packets"
)
def ingest_csi_telemetry(
    payload: Union[CsiIngestBatch, CsiPacketIn],
    device: SensingDevice = Depends(get_authenticated_device),
    session: Session = Depends(get_session)
):
    device_source = device.allowed_source or "live"
    
    if isinstance(payload, CsiIngestBatch):
        if payload.mac_address and payload.mac_address.strip().lower() != device.mac_address.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MAC address mismatch in batch: payload specifies '{payload.mac_address}' but device is registered as '{device.mac_address}'."
            )
        packets_to_process = payload.packets
    else:
        packets_to_process = [payload]

    records: List[RawCsiTelemetry] = []
    now_utc = datetime.now(timezone.utc)

    for p in packets_to_process:
        if p.mac_address and p.mac_address.strip().lower() != device.mac_address.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MAC address mismatch: packet specifies '{p.mac_address}' but device is registered as '{device.mac_address}'."
            )
        
        if p.provenance and p.provenance.strip().lower() != device_source.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provenance conflict: packet specifies '{p.provenance}' but device is restricted to '{device_source}'."
            )
        
        pkt_time = p.timestamp or now_utc
        if pkt_time.tzinfo is None:
            pkt_time = pkt_time.replace(tzinfo=timezone.utc)

        record = RawCsiTelemetry(
            device_id=device.id,
            room_id=device.room_id,
            timestamp=pkt_time,
            sequence_number=p.sequence_number,
            rssi=p.rssi,
            noise_floor=p.noise_floor,
            subcarrier_count=p.subcarrier_count if p.subcarrier_count is not None else 56,
            bandwidth_mhz=p.bandwidth_mhz if p.bandwidth_mhz is not None else 20,
            channel=p.channel,
            csi_data=p.csi_data,
            provenance=device_source,
            created_at=now_utc
        )
        records.append(record)

    for rec in records:
        session.add(rec)

    device.device_status = "ONLINE"
    device.last_seen_at = now_utc
    session.add(device)
    session.commit()
    session.refresh(device)

    det = {"detections": [], "note": None}
    try:
        det = detection.run_detection(session, device, flush=False)
    except Exception as exc:  # packets are already stored; a detector fault must not fail the device upload
        session.rollback()
        det = {"detections": [], "note": f"Detection error ({type(exc).__name__}); packets were stored."}

    return CsiIngestOut(
        status="success",
        device_id=device.id,
        mac_address=device.mac_address,
        room_id=device.room_id,
        ingested_count=len(records),
        provenance=device_source,
        device_status=device.device_status,
        last_seen_at=now_utc,
        detections=det["detections"],
        detection_note=det["note"],
    )


@router.post("/detect", summary="Analyse any complete-enough pending packets now (device-authenticated)")
def flush_detection(
    device: SensingDevice = Depends(get_authenticated_device),
    session: Session = Depends(get_session)
):
    """Used at the end of a recorded clip: processes a final partial window of at least 100 packets."""
    det = detection.run_detection(session, device, flush=True)
    return {"device_id": device.id, "provenance": device.allowed_source, "detections": det["detections"], "note": det["note"]}


@router.get("/model-info", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_model_info():
    """What the detection model is, what it was trained on, and how it scored on people it had never seen."""
    return fall_model.model_info()


def user_can_access_room(user, room_id: Optional[str], session: Session) -> bool:
    scopes = get_user_scopes(user)
    if scopes["is_system_admin"]:
        return True
    room = session.get(Room, room_id) if room_id else None
    flr = session.get(Floor, room.floor_id) if room else None
    bld = session.get(Building, flr.building_id) if flr else None
    return bool(bld and (bld.organization_id in scopes["organization_ids"] or bld.id in scopes["building_ids"]
                         or room.id in scopes["room_ids"]))

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
    device.last_seen_at = datetime.now(timezone.utc)
    session.add(device)

    activity_name = event_data.simulated_activity
    if activity_name not in ACTIVITY_MAPPING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid simulated activity name. Allowed: {list(ACTIVITY_MAPPING.keys())}")

    activity_id, category = ACTIVITY_MAPPING[activity_name]
    profile = DETERMINISTIC_PROFILES.get(activity_name, DETERMINISTIC_PROFILES["Presence"])

    # Optional overrides let staff/tests demonstrate low-confidence handling. The event stays SIMULATED either way.
    sim_confidence = event_data.confidence if event_data.confidence is not None else profile["confidence"]
    sim_signal_quality = event_data.signal_quality if event_data.signal_quality is not None else profile["signal_quality"]

    sensing_event = SensingEvent(
        device_id=device.id,
        room_id=room.id,
        timestamp=datetime.now(timezone.utc),
        rssi=profile["rssi"],
        subcarrier_count=profile["subcarriers"],
        signal_quality=sim_signal_quality,
        event_type=profile["event_type"],
        raw_csi_payload_path=None,
        extracted_features=profile["features"],
        inferred_activity_id=activity_id,
        model_confidence=sim_confidence,
        source="simulated"
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
        alert_msg = f"Critical Fall Detected in Room {room.name}! [SIMULATED]"
        db_alert = Alert(
            room_id=room.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message=alert_msg,
            status="new",
            source="simulated",
            device_id=device.id,
            confidence=sim_confidence,
            signal_quality=sim_signal_quality
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
            "timestamp": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M:%S"),
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
            "signal_level": signal_level(sensing_event.signal_quality),
            "confidence_level": confidence_level(sensing_event.model_confidence),
            "requires_verification": requires_verification(sensing_event.model_confidence, sensing_event.signal_quality),
            "source": sensing_event.source,
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

@router.get("/history", response_model=List[SensingHistoryOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_detection_history(
    room_id: Optional[str] = None,
    source: Optional[str] = Query(default=None, pattern="^(simulated|dataset|live)$"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Recent detections with confidence, signal quality and source, limited to the caller's organization scope."""
    scopes = get_user_scopes(current_user)
    stmt = select(SensingEvent, ActivityType, Room).join(ActivityType, ActivityType.id == SensingEvent.inferred_activity_id).join(Room, Room.id == SensingEvent.room_id)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Floor, Floor.id == Room.floor_id).join(Building, Building.id == Floor.building_id).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))
    if room_id:
        stmt = stmt.where(SensingEvent.room_id == room_id)
    if source:
        stmt = stmt.where(SensingEvent.source == source)
    rows = session.exec(stmt.order_by(SensingEvent.timestamp.desc()).limit(limit)).all()
    ev_ids = [ev.id for ev, _, _ in rows]
    labels = {e.event_id: e.recorded_label for e in session.exec(
        select(ReplayEvaluation).where(ReplayEvaluation.event_id.in_(ev_ids))).all()} if ev_ids else {}
    macs = {d.id: d.mac_address for d in session.exec(
        select(SensingDevice).where(SensingDevice.id.in_([ev.device_id for ev, _, _ in rows]))).all()} if rows else {}
    return [
        SensingHistoryOut(
            id=ev.id,
            timestamp=ev.timestamp,
            room_id=ev.room_id,
            room_name=rm.name,
            device_id=ev.device_id,
            activity=act.name,
            category=act.category,
            confidence=ev.model_confidence,
            confidence_level=confidence_level(ev.model_confidence),
            signal_quality=ev.signal_quality,
            signal_level=signal_level(ev.signal_quality),
            rssi=ev.rssi,
            source=ev.source,
            requires_verification=(act.name == "Possible_Fall") or requires_verification(ev.model_confidence, ev.signal_quality),
            noise_floor=(ev.extracted_features or {}).get("noise_floor_median"),
            subcarrier_count=ev.subcarrier_count if ev.source != "simulated" else None,
            window_packets=(ev.extracted_features or {}).get("window_packets"),
            fall_score=(ev.extracted_features or {}).get("fall_score"),
            model=(ev.extracted_features or {}).get("model"),
            device_mac=macs.get(ev.device_id),
            recorded_label=labels.get(ev.id),
        )
        for ev, act, rm in rows
    ]

@router.get("/devices/{device_id}/csi-telemetry", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_device_csi_telemetry(
    device_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """What this device has REALLY sent. Nothing here is generated: a device that has sent no packets reports none.

    The mode is derived from the registered provenance of the device: DEMO, DATASET REPLAY or LIVE HARDWARE."""
    device = session.get(SensingDevice, device_id)
    if not device or not user_can_access_room(current_user, device.room_id, session):
        raise HTTPException(status_code=404, detail="Device not found.")  # same answer for missing and for not yours

    source = device.allowed_source or "live"
    mode = {"simulated": "DEMO", "dataset": "DATASET REPLAY", "live": "LIVE HARDWARE"}.get(source, source.upper())
    room = session.get(Room, device.room_id) if device.room_id else None
    total = session.exec(select(func.count()).select_from(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id)).one()
    recent = session.exec(
        select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id).order_by(RawCsiTelemetry.id.desc()).limit(200)
    ).all()
    last_event = session.exec(
        select(SensingEvent).where(SensingEvent.device_id == device_id, SensingEvent.event_type == "DetectionWindow")
        .order_by(SensingEvent.id.desc())
    ).first()
    act = session.get(ActivityType, last_event.inferred_activity_id) if last_event else None

    out: Dict[str, Any] = {
        "device_id": device.id, "mac_address": device.mac_address, "room_name": room.name if room else None,
        "mode": mode, "provenance": source, "device_status": device.device_status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "packets_total": int(total), "has_data": bool(recent),
        "data_statement": {
            "DEMO": "Demonstration data. No CSI packets come from this device.",
            "DATASET REPLAY": "Recorded CSI replayed through the ingest pipeline. This is not current sensing.",
            "LIVE HARDWARE": "Packets received from this authenticated device.",
        }.get(mode),
    }
    if recent:
        last = recent[0]
        rssi = sorted(r.rssi for r in recent)
        noise = sorted(r.noise_floor for r in recent if r.noise_floor is not None)
        arrivals = sorted(r.created_at for r in recent if r.created_at)
        span = (arrivals[-1] - arrivals[0]).total_seconds() if len(arrivals) > 1 else 0
        iq = (last.csi_data or {}).get("iq") if isinstance(last.csi_data, dict) else None
        amplitude = None
        if isinstance(iq, list) and len(iq) % 2 == 0:
            amplitude = [round((iq[i] ** 2 + iq[i + 1] ** 2) ** 0.5, 2) for i in range(0, len(iq), 2)]
        out.update({
            "last_packet": {
                "timestamp": last.timestamp.isoformat() if last.timestamp else None,
                "received_at": last.created_at.isoformat() if last.created_at else None,
                "sequence_number": last.sequence_number, "rssi_dbm": last.rssi, "noise_floor_dbm": last.noise_floor,
                "subcarrier_count": last.subcarrier_count, "channel": last.channel, "bandwidth_mhz": last.bandwidth_mhz,
            },
            "recent_window": {
                "packets": len(recent),
                "rssi_median_dbm": float(rssi[len(rssi) // 2]),
                "noise_floor_median_dbm": float(noise[len(noise) // 2]) if noise else None,
                "arrival_rate_hz": round((len(arrivals) - 1) / span, 1) if span > 0 else None,
            },
            "amplitude_last_packet": amplitude,
        })
    out["latest_detection"] = ({
        "event_id": last_event.id, "activity": act.name if act else None, "confidence": round(last_event.model_confidence, 3),
        "signal_quality": last_event.signal_quality, "timestamp": last_event.timestamp.isoformat(),
        "fall_score": (last_event.extracted_features or {}).get("fall_score"), "source": last_event.source,
    } if last_event else None)
    return out
