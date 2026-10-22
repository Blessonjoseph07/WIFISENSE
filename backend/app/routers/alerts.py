from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import Alert, AlertAcknowledgement, Room, Floor, Building, Resident, EmergencyContact, SensingEvent, ActivityType, Organization, User, SensingDevice
from app.schemas.schemas import AlertOut, AlertResolve, AlertDetailOut, AlertAcknowledgementOut, AlertVerify
from app.core.audit import record_audit_event
from app.core.confidence import confidence_level, signal_level

router = APIRouter(prefix="/alerts", tags=["Alert Engine"])

STAFF_ROLES = ["system_admin", "facility_manager", "caregiver", "corporate_staff"]
CARE_RESPONDER_ROLES = ["facility_manager", "caregiver"]

def get_scoped_alert_query(scopes):
    stmt = select(Alert)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Room).join(Floor).join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))
    return stmt

def _evidence_fields(alert: Alert, session: Session) -> Dict[str, Any]:
    """Detection evidence + verification fields shared by the list and detail responses."""
    device = session.get(SensingDevice, alert.device_id) if alert.device_id else None
    verifier = session.get(User, alert.verified_by) if alert.verified_by else None
    return dict(
        source=alert.source,
        device_id=alert.device_id,
        device_mac=device.mac_address if device else None,
        confidence=alert.confidence,
        signal_quality=alert.signal_quality,
        verification_status=alert.verification_status,
        verified_by_name=f"{verifier.first_name} {verifier.last_name}" if verifier else None,
        verified_at=alert.verified_at,
        verification_note=alert.verification_note,
    )

def enrich_alerts(alerts: List[Alert], session: Session) -> List[AlertOut]:
    if not alerts:
        return []
    
    rooms_map = {r.id: r for r in session.exec(select(Room)).all()}
    floors_map = {f.id: f for f in session.exec(select(Floor)).all()}
    blds_map = {b.id: b for b in session.exec(select(Building)).all()}
    orgs_map = {o.id: o for o in session.exec(select(Organization)).all()}
    residents_by_room = {}
    for res in session.exec(select(Resident)).all():
        residents_by_room.setdefault(res.room_id, []).append(f"{res.first_name} {res.last_name}")
    
    out = []
    for alert in alerts:
        room = rooms_map.get(alert.room_id)
        flr = floors_map.get(room.floor_id) if room else None
        bld = blds_map.get(flr.building_id) if flr else None
        org = orgs_map.get(bld.organization_id) if bld else None
        
        resident_name = None
        if org and org.type == "ELDER_CARE" and room:
            names = residents_by_room.get(room.id)
            if names:
                resident_name = ", ".join(names)
                
        out.append(AlertOut(
            id=alert.id,
            alert_configuration_id=getattr(alert, "alert_configuration_id", None),
            room_id=alert.room_id,
            event_type=alert.event_type,
            severity=alert.severity,
            message=alert.message,
            status=alert.status,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            room_name=room.name if room else None,
            floor_number=flr.floor_number if flr else None,
            building_name=bld.name if bld else None,
            organization_id=org.id if org else None,
            organization_name=org.name if org else None,
            organization_type=org.type if org else None,
            resident_name=resident_name,
            **_evidence_fields(alert, session)
        ))
    return out

@router.get("", response_model=List[AlertOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_alerts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).order_by(Alert.created_at.desc())
    alerts = session.exec(stmt).all()
    return enrich_alerts(alerts, session)

@router.get("/active", response_model=List[AlertOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_active_alerts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(Alert.status.in_(["new", "acknowledged", "responding"])).order_by(Alert.created_at.desc())
    alerts = session.exec(stmt).all()
    return enrich_alerts(alerts, session)

# ============================================================================
# EMERGENCY FALL PROTOCOL DYNAMIC DATA REFRESH (PHASE 5 & 5A)
# ============================================================================

@router.get("/emergency-active", dependencies=[Depends(require_roles(["system_admin", "facility_manager", "caregiver"]))])
def get_active_fall_emergency(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(
        Alert.status.in_(["new", "acknowledged", "responding"]),
        Alert.event_type == "Fall_Detected"
    ).order_by(Alert.created_at.desc())
    alert = session.exec(stmt).first()

    if not alert:
        return {"has_emergency": False}

    room = session.get(Room, alert.room_id)
    resident = session.exec(select(Resident).where(Resident.room_id == alert.room_id)).first() if room else None
    
    # Retrieve emergency contact
    primary_contact = None
    if resident:
        contacts = session.exec(
            select(EmergencyContact).where(EmergencyContact.resident_id == resident.id).order_by(EmergencyContact.priority)
        ).all()
        if contacts:
            primary_contact = contacts[0]

    evidence = _evidence_fields(alert, session)
    verification_needed = AlertOut.model_validate(alert).requires_verification

    return {
        "has_emergency": True,
        "alert_id": alert.id,
        "status": alert.status,
        "resident_id": resident.id if resident else None,
        "resident_name": f"{resident.first_name} {resident.last_name}" if resident else "Elder Care Resident",
        "room_id": room.id if room else alert.room_id,
        "room_name": room.name if room else None,
        "detected_at": alert.created_at.strftime("%d %b %Y %H:%M:%S"),
        "activity": "Fall Detected",
        "severity": alert.severity,
        "message": alert.message,
        "source": alert.source,
        "device_mac": evidence["device_mac"],
        "verification_status": alert.verification_status,
        "requires_verification": verification_needed,
        # Real values copied from the detecting event at alert time; null when the alert carries no sensing evidence.
        "telemetry": {
            "signal_quality": alert.signal_quality,
            "signal_level": signal_level(alert.signal_quality),
            "confidence": round(alert.confidence * 100, 1) if alert.confidence is not None else None,
            "confidence_level": confidence_level(alert.confidence),
        },
        "emergency_contact": {
            "name": primary_contact.name,
            "relationship": primary_contact.relationship,
            "phone": primary_contact.phone,
            "priority": primary_contact.priority
        } if primary_contact else None  # no invented fallback: the UI must say "no emergency contact on file"
    }

@router.get("/{alert_id}", response_model=AlertDetailOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_alert_detail(
    alert_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(Alert.id == alert_id)
    alert = session.exec(stmt).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found or access denied.")

    room = session.get(Room, alert.room_id)
    flr = session.get(Floor, room.floor_id) if room else None
    bld = session.get(Building, flr.building_id) if flr else None
    org = session.get(Organization, bld.organization_id) if bld else None
    
    # Resident & emergency contacts ONLY for ELDER_CARE:
    resident = None
    if org and org.type == "ELDER_CARE" and room:
        resident = session.exec(select(Resident).where(Resident.room_id == alert.room_id)).first()

    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    ack_out = None
    if ack:
        ack_user = session.get(User, ack.user_id) if ack.user_id else None
        ack_out = AlertAcknowledgementOut(
            id=ack.id,
            alert_id=ack.alert_id,
            user_id=ack.user_id,
            who_user_id=ack.user_id,
            user_email=ack_user.email if ack_user else None,
            user_name=f"{ack_user.first_name} {ack_user.last_name}" if ack_user else None,
            acknowledged_at=ack.acknowledged_at,
            resolved_at=ack.resolved_at,
            resolution_notes=ack.resolution_notes
        )

    emergency_contact = None
    if resident:
        contacts = session.exec(
            select(EmergencyContact).where(EmergencyContact.resident_id == resident.id).order_by(EmergencyContact.priority)
        ).all()
        if contacts:
            primary = contacts[0]
            emergency_contact = {
                "name": primary.name,
                "relationship": primary.relationship,
                "phone": primary.phone,
                "priority": primary.priority
            }

    return AlertDetailOut(
        id=alert.id,
        alert_configuration_id=getattr(alert, "alert_configuration_id", None),
        room_id=alert.room_id,
        event_type=alert.event_type,
        severity=alert.severity,
        message=alert.message,
        status=alert.status,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        room_name=room.name if room else None,
        floor_number=flr.floor_number if flr else None,
        building_name=bld.name if bld else None,
        organization_id=org.id if org else None,
        organization_name=org.name if org else None,
        organization_type=org.type if org else None,
        resident_id=resident.id if resident else None,
        resident_name=f"{resident.first_name} {resident.last_name}" if resident else None,
        acknowledgement=ack_out,
        emergency_contact=emergency_contact,
        **_evidence_fields(alert, session)
    )

@router.patch("/{alert_id}/verify", response_model=AlertDetailOut, dependencies=[Depends(require_roles(CARE_RESPONDER_ROLES))])
def verify_alert(
    alert_id: str,
    body: AlertVerify,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Staff confirm or dismiss a detection. The outcome is stored for later analytics."""
    scopes = get_user_scopes(current_user)
    alert = session.exec(get_scoped_alert_query(scopes).where(Alert.id == alert_id)).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found or access denied.")
    if alert.verification_status != "UNVERIFIED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Alert already {alert.verification_status.lower()}.")
    if body.outcome == "DISMISSED" and not (body.note and body.note.strip()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A note is required when dismissing a detection.")

    now = datetime.now(timezone.utc)
    alert.verification_status = body.outcome
    alert.verified_by = current_user.id
    alert.verified_at = now
    alert.verification_note = body.note.strip() if body.note else None
    alert.updated_at = now
    if body.outcome == "DISMISSED":
        # A dismissed detection is a false alarm: close the alert and keep who/why on the acknowledgement.
        alert.status = "resolved"
        ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
        if not ack:
            ack = AlertAcknowledgement(alert_id=alert.id, user_id=current_user.id, acknowledged_at=now)
        ack.resolved_at = now
        ack.resolution_notes = f"Dismissed as false alarm: {alert.verification_note}"
        session.add(ack)
    session.add(alert)
    session.commit()
    session.refresh(alert)

    record_audit_event(
        session=session,
        what_action=f"ALERT_{body.outcome}",
        resource_type="ALERT",
        resource_id=alert.id,
        result="SUCCESS",
        who_user_id=current_user.id,
        who_email=current_user.email,
        details={
            "confidence": alert.confidence,
            "signal_quality": alert.signal_quality,
            "source": alert.source,
            "room_id": alert.room_id,
        }
    )
    return get_alert_detail(alert_id, session, current_user)

@router.patch("/{alert_id}/acknowledge", response_model=AlertOut, dependencies=[Depends(require_roles(CARE_RESPONDER_ROLES))])
def acknowledge_alert(
    alert_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(Alert.id == alert_id)
    alert = session.exec(stmt).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found or access denied.")

    if alert.status == "acknowledged":
        return alert
    if alert.status == "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is already resolved.")

    alert.status = "acknowledged"
    alert.updated_at = datetime.now(timezone.utc)
    session.add(alert)

    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    if not ack:
        ack = AlertAcknowledgement(
            alert_id=alert.id,
            user_id=current_user.id,
            acknowledged_at=datetime.now(timezone.utc)
        )
    else:
        ack.user_id = current_user.id
        ack.acknowledged_at = datetime.now(timezone.utc)
    session.add(ack)
    session.commit()
    session.refresh(alert)

    room = session.get(Room, alert.room_id)
    flr = session.get(Floor, room.floor_id) if room else None
    bld = session.get(Building, flr.building_id) if flr else None

    record_audit_event(
        session=session,
        what_action="ALERT_ACKNOWLEDGED",
        resource_type="ALERT",
        resource_id=alert.id,
        result="SUCCESS",
        who_user_id=current_user.id,
        who_email=current_user.email,
        details={
            "status": alert.status,
            "room_id": alert.room_id,
            "organization_id": bld.organization_id if bld else None
        }
    )

    return alert

@router.patch("/{alert_id}/responding", response_model=AlertOut, dependencies=[Depends(require_roles(CARE_RESPONDER_ROLES))])
def mark_alert_responding(
    alert_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(Alert.id == alert_id)
    alert = session.exec(stmt).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found or access denied.")

    if alert.status == "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is already resolved.")

    alert.status = "responding"
    alert.updated_at = datetime.now(timezone.utc)
    session.add(alert)

    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    if not ack:
        ack = AlertAcknowledgement(
            alert_id=alert.id,
            user_id=current_user.id,
            acknowledged_at=datetime.now(timezone.utc)
        )
        session.add(ack)
    
    session.commit()
    session.refresh(alert)

    room = session.get(Room, alert.room_id)
    flr = session.get(Floor, room.floor_id) if room else None
    bld = session.get(Building, flr.building_id) if flr else None

    record_audit_event(
        session=session,
        what_action="ALERT_RESPONDING",
        resource_type="ALERT",
        resource_id=alert.id,
        result="SUCCESS",
        who_user_id=current_user.id,
        who_email=current_user.email,
        details={
            "status": alert.status,
            "room_id": alert.room_id,
            "organization_id": bld.organization_id if bld else None
        }
    )

    return alert

@router.patch("/{alert_id}/resolve", response_model=AlertOut, dependencies=[Depends(require_roles(CARE_RESPONDER_ROLES))])
def resolve_alert(
    alert_id: str,
    resolution_data: AlertResolve,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(Alert.id == alert_id)
    alert = session.exec(stmt).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found or access denied.")

    if alert.status == "resolved":
        return alert

    alert.status = "resolved"
    alert.updated_at = datetime.now(timezone.utc)
    session.add(alert)

    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    if not ack:
        ack = AlertAcknowledgement(
            alert_id=alert.id,
            user_id=current_user.id,
            acknowledged_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc),
            resolution_notes=resolution_data.resolution_notes
        )
    else:
        ack.resolved_at = datetime.now(timezone.utc)
        ack.resolution_notes = resolution_data.resolution_notes
    session.add(ack)

    session.commit()
    session.refresh(alert)

    room = session.get(Room, alert.room_id)
    flr = session.get(Floor, room.floor_id) if room else None
    bld = session.get(Building, flr.building_id) if flr else None

    record_audit_event(
        session=session,
        what_action="ALERT_RESOLVED",
        resource_type="ALERT",
        resource_id=alert.id,
        result="SUCCESS",
        who_user_id=current_user.id,
        who_email=current_user.email,
        details={
            "status": alert.status,
            "room_id": alert.room_id,
            "organization_id": bld.organization_id if bld else None,
            "resolution_notes": resolution_data.resolution_notes
        }
    )

    return alert

