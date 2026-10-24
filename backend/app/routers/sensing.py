import secrets
import time
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header, Request, Response, Query
from sqlalchemy import insert
from sqlmodel import Session, select, or_, func
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from app.core.config import settings
from app.core.database import get_session
from app.core.security import hash_token
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import SensingDevice, Room, Floor, Building, SensingEvent, ActivityType, Alert, RoomCalibration, RawCsiTelemetry, ReplayEvaluation
from app.schemas.schemas import SensingEventSimulate, CsiPacketIn, CsiIngestBatch, CsiIngestOut, SensingHistoryOut
from app.core.confidence import confidence_level, signal_level, requires_verification
from app.services.notifications import process_alert_notifications
from app.services import detection, fall_model, csi_physics, ingest_metrics, movement
from app.core.audit import record_audit_event

router = APIRouter(prefix="/sensing", tags=["Sensing Pipeline"])
STAFF_ROLES = ["system_admin", "facility_manager", "caregiver", "corporate_staff"]
MAX_INGEST_PAYLOAD_BYTES = 64 * 1024  # 64 KB maximum request/payload limit
# A device an admin has pulled for repair must not flip itself back to ONLINE by sending packets.
# OFFLINE is deliberately allowed: a newly registered device starts OFFLINE and becomes ONLINE on first packet.
INGEST_BLOCKED_STATUSES = {"FAULT_REPORTED", "INSPECTING", "SERVICING"}

def start_ingest_timer(request: Request):
    """First dependency of /ingest: marks when the server began working on the request (reported as server_ms)."""
    request.state.t0 = time.perf_counter()


def _header_number(request: Request, name: str, cast=float, lo=0, hi=10 ** 9):
    try:
        v = cast(request.headers.get(name, ""))
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


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
    dependencies=[Depends(start_ingest_timer), Depends(verify_ingest_payload_size)],
    summary="Ingest Raw CSI Telemetry Packets"
)
def ingest_csi_telemetry(
    payload: Union[CsiIngestBatch, CsiPacketIn],
    request: Request,
    response: Response,
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

    rows: List[Dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)
    packet_times: List[datetime] = []

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
        if p.timestamp:
            packet_times.append(pkt_time)

        rows.append(dict(
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
            created_at=now_utc,
            event_id=None,
        ))

    # One multi-row INSERT instead of one object per packet: this is the hot path.
    session.execute(insert(RawCsiTelemetry), rows)

    device.device_status = "ONLINE"
    device.last_seen_at = now_utc
    session.add(device)
    session.commit()

    det = {"detections": [], "note": None}
    try:
        det = detection.run_detection(session, device, flush=False)
    except Exception as exc:  # packets are already stored; a detector fault must not fail the device upload
        session.rollback()
        det = {"detections": [], "note": f"Detection error ({type(exc).__name__}); packets were stored."}

    server_ms = round((time.perf_counter() - getattr(request.state, "t0", time.perf_counter())) * 1000, 2)
    response.headers["X-Process-Ms"] = str(server_ms)
    ingest_metrics.record(
        device.id, len(rows), server_ms,
        delay_oldest_ms=round((now_utc - min(packet_times)).total_seconds() * 1000, 1) if packet_times else None,
        delay_newest_ms=round((now_utc - max(packet_times)).total_seconds() * 1000, 1) if packet_times else None,
        client_rtt_ms=_header_number(request, "X-Client-Rtt-Ms", float, 0, 600000),
        client_queue=_header_number(request, "X-Client-Queue", int, 0, 10 ** 7),
        client_dropped=_header_number(request, "X-Client-Dropped", int, 0, 10 ** 9),
    )

    return CsiIngestOut(
        status="success",
        device_id=device.id,
        mac_address=device.mac_address,
        room_id=device.room_id,
        ingested_count=len(rows),
        provenance=device_source,
        device_status=device.device_status,
        last_seen_at=now_utc,
        detections=det["detections"],
        detection_note=det["note"],
        server_ms=server_ms,
    )


@router.post("/detect", summary="Analyse any complete-enough pending packets now (device-authenticated)")
def flush_detection(
    device: SensingDevice = Depends(get_authenticated_device),
    session: Session = Depends(get_session)
):
    """Used at the end of a recorded clip: processes a final partial window of at least 100 packets."""
    det = detection.run_detection(session, device, flush=True)
    return {"device_id": device.id, "provenance": device.allowed_source, "detections": det["detections"], "note": det["note"]}


@router.get("/retention", dependencies=[Depends(require_roles(["system_admin", "facility_manager"]))])
def raw_csi_retention(session: Session = Depends(get_session)):
    """The raw-CSI retention policy, how full the table is, and what the last prune removed."""
    from app.services import retention
    return retention.retention_status(session)


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


MOVEMENT_CAVEATS = [
    "This shows movement on the Wi-Fi link between the two boards. It does not count, locate or identify people.",
    "A person standing or lying completely still barely changes the signal, so 'quiet' does not mean 'nobody is there'.",
    "Presence is judged against an empty-room reference. Until you record one in this room it uses a default reference from a quiet-room recording with these boards, so treat the first readings as approximate.",
    "A fan, a door, a pet or someone in the next room can also raise it. Recalibrate when the room changes.",
]
MOVEMENT_BLOCKS_SHOWN = 24
STALE_SECONDS = 20


def _movement_device(device_id: str, session: Session, current_user) -> SensingDevice:
    device = session.get(SensingDevice, device_id)
    if not device or not user_can_access_room(current_user, device.room_id, session):
        raise HTTPException(status_code=404, detail="Device not found.")
    return device


def _calibration(session: Session, device_id: str) -> Optional[RoomCalibration]:
    return session.exec(select(RoomCalibration).where(RoomCalibration.device_id == device_id)).first()


def _recent_records(session: Session, device_id: str, n: int):
    rows = session.exec(
        select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id).order_by(RawCsiTelemetry.id.desc()).limit(n)
    ).all()
    rows.reverse()
    return rows


def _human_duration(seconds: float) -> str:
    s = int(seconds)
    if s < 120:
        return f"{s} seconds"
    if s < 7200:
        return f"{s // 60} minutes"
    if s < 172800:
        return f"{s // 3600} hours"
    return f"{s // 86400} days"


def _seconds_since(dt) -> Optional[float]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())


@router.get("/devices/{device_id}/movement", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_device_movement(
    device_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Is the signal between the boards fluctuating more than it does in an empty, still room? Computed from the device's own
    stored packets, nothing is generated. See app/services/movement.py for exactly what this can and cannot say."""
    device = _movement_device(device_id, session, current_user)

    def build():
        records = _recent_records(session, device_id, MOVEMENT_BLOCKS_SHOWN * movement.BLOCK)
        blocks = movement.block_variations(records)[-MOVEMENT_BLOCKS_SHOWN:]
        cal = _calibration(session, device_id)
        baseline = ((cal.subcarrier_profile or {}).get("movement_baseline") if cal else None)
        verdict = movement.classify(blocks, baseline)
        if baseline is None and blocks:
            baseline_view = dict(movement.DEFAULT_REFERENCE)
        else:
            baseline_view = baseline
        idle = _seconds_since(records[-1].created_at) if records else None
        if records and idle is not None and idle > STALE_SECONDS:
            verdict = {"state": "STALE", "headline": "Board is not sending",
                       "detail": f"The last packet arrived {_human_duration(idle)} ago, so there is no current reading."}
        return {"state": verdict["state"], "headline": verdict["headline"], "detail": verdict["detail"],
                "activity_ratio": verdict.get("activity_ratio"), "presence": verdict["state"] in ("PRESENT", "MOVEMENT"),
                "reference": verdict.get("reference"),
                "blocks": [round(b, 4) for b in blocks], "baseline": baseline,
                "threshold": baseline_view["threshold"] if baseline_view else None,
                "reference_mean": baseline_view["mean"] if baseline_view else None,
                "seconds_since_last_packet": round(idle, 1) if idle is not None else None,
                "block_packets": movement.BLOCK}
    out = dict(movement.cached(f"{device_id}", build))
    source = device.allowed_source or "live"
    out.update({
        "device_id": device.id, "mode": {"simulated": "DEMO", "dataset": "DATASET REPLAY", "live": "LIVE HARDWARE"}.get(source, source.upper()),
        "caveats": MOVEMENT_CAVEATS,
        "fall_detection": "on (experimental)" if (source == "live" and settings.LIVE_FALL_DETECTION) else
                          ("off for live hardware: the model has not been validated in this room" if source == "live" else "not applicable"),
    })
    return out


@router.post("/devices/{device_id}/movement/baseline", dependencies=[Depends(require_roles(["system_admin", "facility_manager"]))])
def record_movement_baseline(
    device_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Record the empty-room reference from the packets the device is sending right now. The operator must make sure the room
    is empty and still for about 15 seconds first; an unstable reference is refused."""
    device = _movement_device(device_id, session, current_user)
    records = _recent_records(session, device_id, 12 * movement.BLOCK)
    idle = _seconds_since(records[-1].created_at) if records else None
    if idle is None or idle > 30:
        raise HTTPException(status_code=409, detail="The board is not sending right now. Start it, wait a few seconds, and try again.")
    blocks = movement.block_variations(records)
    baseline = movement.baseline_from(blocks)
    if not baseline:
        raise HTTPException(status_code=409, detail=f"Not enough readings yet: need about {movement.MIN_BASELINE_BLOCKS * movement.BLOCK} packets, have {len(records)}.")
    if baseline["mean"] > 0 and baseline["std"] / baseline["mean"] > 0.6:
        raise HTTPException(status_code=409, detail="The signal was changing too much to be an empty, still room. Leave the room, wait 15 seconds and try again.")
    cal = _calibration(session, device_id)
    profile = dict((cal.subcarrier_profile or {}) if cal else {})
    profile["movement_baseline"] = baseline
    if cal:
        cal.subcarrier_profile = profile
        cal.baseline_captured_at = datetime.now(timezone.utc)
        cal.updated_at = datetime.now(timezone.utc)
        session.add(cal)
    else:
        session.add(RoomCalibration(room_id=device.room_id, device_id=device.id, subcarrier_profile=profile))
    session.commit()
    with movement._cache_lock:
        movement._cache.pop(f"{device_id}", None)
    record_audit_event(session=session, what_action="MOVEMENT_BASELINE_RECORDED", resource_type="DEVICE", resource_id=device.id,
                       who_user_id=current_user.id, who_email=current_user.email,
                       details={"blocks": baseline["blocks"], "mean": baseline["mean"], "threshold": baseline["threshold"]}, request=request)
    return {"device_id": device.id, "baseline": baseline, "note": "Movement is now judged against this empty-room reference."}


@router.get("/devices/{device_id}/live", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_device_live_stream(
    device_id: str,
    after_id: int = Query(0, ge=0, description="Return only packets stored after this id (incremental polling)"),
    window: int = Query(60, ge=8, le=200, description="Packets used for the statistics"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Real-time view of what a device has sent: per-packet amplitude and phase per subcarrier plus link statistics.

    Same access rule and same honesty rule as csi-telemetry: nothing is generated here, a silent device returns no
    packets, and `mode` says whether the packets are DEMO, DATASET REPLAY or LIVE HARDWARE. There are no x/y
    coordinates in the result: one transmitter-receiver pair cannot provide them."""
    device = session.get(SensingDevice, device_id)
    if not device or not user_can_access_room(current_user, device.room_id, session):
        raise HTTPException(status_code=404, detail="Device not found.")

    source = device.allowed_source or "live"
    mode = {"simulated": "DEMO", "dataset": "DATASET REPLAY", "live": "LIVE HARDWARE"}.get(source, source.upper())
    rows = session.exec(
        select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id).order_by(RawCsiTelemetry.id.desc()).limit(window)
    ).all()
    rows.reverse()

    parsed: List[Dict[str, Any]] = []
    for r in rows:
        data = r.csi_data if isinstance(r.csi_data, dict) else {}
        ap = csi_physics.iq_to_amp_phase(data.get("iq"))
        parsed.append({
            "id": r.id, "seq": r.sequence_number, "rssi": r.rssi, "noise": r.noise_floor,
            "t": r.created_at.replace(tzinfo=r.created_at.tzinfo or timezone.utc).timestamp() if r.created_at else None,
            "ts": r.timestamp.isoformat() if r.timestamp else None,
            "channel": r.channel, "bandwidth_mhz": r.bandwidth_mhz,
            "amp": ap["amplitude"] if ap else None, "phase": ap["phase"] if ap else None,
            "meta": {k: data[k] for k in ("src_mac", "rate", "sig_mode", "mcs", "cwb", "smoothing", "not_sounding",
                                          "aggregation", "stbc", "fec_coding", "sgi", "ant", "agc_gain", "fft_gain")
                     if k in data},
        })

    last = rows[-1] if rows else None
    link = csi_physics.link_info(last.channel if last else None, last.bandwidth_mhz if last else None)
    new_packets = [
        {"id": p["id"], "seq": p["seq"], "timestamp": p["ts"], "rssi_dbm": p["rssi"], "noise_floor_dbm": p["noise"],
         "snr_db": (p["rssi"] - p["noise"]) if p["noise"] is not None else None,
         "amplitude": p["amp"], "phase": p["phase"], "meta": p["meta"]}
        for p in parsed if p["id"] > after_id
    ]
    total = session.exec(select(func.count()).select_from(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id)).one()
    return {
        "device_id": device.id, "mac_address": device.mac_address, "mode": mode, "provenance": source,
        "device_status": device.device_status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "packets_total": int(total), "has_data": bool(rows),
        "link": link,
        "stats": csi_physics.window_stats(parsed),
        "latest_id": rows[-1].id if rows else after_id,
        "packets": new_packets,
        "delivery": ingest_metrics.summary(device_id),
        "limits": "No x/y position is reported: a single transmitter-receiver pair measures the channel between two radios, "
                  "not where a person stands. Wavelength is derived from the reported channel number.",
    }
