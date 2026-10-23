from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, or_
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.core.audit import record_audit_event
from app.core.database import get_session
from app.core.timeutil import as_utc, utcnow
from app.services.payments import lifecycle
from app.services.payments.webhooks import subscription_org_id
from app.routers.auth import get_current_user, require_roles, get_user_scopes, get_user_role_and_context
from app.models.entities import (
    User, AccessRequest, FamilyConnection, FamilySubscription,
    Resident, SensingEvent, ActivityType, Alert, Room, Floor, Building, Organization, SharingPolicy
)
from app.schemas.schemas import (
    AccessRequestCreate, AccessRequestOut, AccessRequestReview,
    FamilyConnectionCreate, FamilyConnectionReview, FamilyConnectionOut,
    FamilySubscriptionOut, FamilySubscriptionUpdate
)

router = APIRouter(prefix="/family", tags=["Family Portal"])

# ============================================================================
# 1. FAMILY CONNECTIONS WORKFLOW (PHASE 3 & 3A)
# ============================================================================

@router.post("/connections", response_model=FamilyConnectionOut, status_code=status.HTTP_201_CREATED)
def submit_family_connection(
    conn_in: FamilyConnectionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name != "family_member" or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered family members in elder-care context can request resident connections."
        )

    resident = session.get(Resident, conn_in.resident_id)
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target elder-care resident not found.")

    room = session.get(Room, resident.room_id)
    floor = session.get(Floor, room.floor_id) if room else None
    building = session.get(Building, floor.building_id) if floor else None
    org = session.get(Organization, building.organization_id) if building else None
    if not org or org.type != "ELDER_CARE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Connections can only be requested for ELDER_CARE residents.")

    # Check for existing active or pending connection
    existing = session.exec(
        select(FamilyConnection).where(
            FamilyConnection.family_user_id == current_user.id,
            FamilyConnection.resident_id == conn_in.resident_id,
            FamilyConnection.status.in_(["pending", "approved"])
        )
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"A {existing.status} connection already exists for this resident.")

    db_conn = FamilyConnection(
        id=str(uuid.uuid4()),
        resident_id=conn_in.resident_id,
        family_user_id=current_user.id,
        relationship=conn_in.relationship,
        status="pending",
        notes=conn_in.notes,
        requested_at=datetime.now(timezone.utc)
    )
    session.add(db_conn)

    # Ensure a pending or active FamilySubscription exists for this family user
    sub = session.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == current_user.id)).first()
    if not sub:
        sub = FamilySubscription(
            id=str(uuid.uuid4()),
            family_user_id=current_user.id,
            family_connection_id=db_conn.id,
            plan="CARE_MONTHLY",
            status="PENDING"
        )
        session.add(sub)

    session.commit()
    session.refresh(db_conn)

    return FamilyConnectionOut(
        id=db_conn.id,
        resident_id=db_conn.resident_id,
        resident_name=f"{resident.first_name} {resident.last_name}",
        room_name=room.name if room else "Room",
        family_user_id=current_user.id,
        family_user_name=f"{current_user.first_name} {current_user.last_name}",
        family_user_email=current_user.email,
        relationship=db_conn.relationship,
        status=db_conn.status,
        requested_at=db_conn.requested_at,
        approved_at=db_conn.approved_at,
        approved_by=db_conn.approved_by,
        notes=db_conn.notes,
        subscription_status=sub.status if sub else "PENDING",
        created_at=db_conn.created_at,
        updated_at=db_conn.updated_at
    )

@router.get("/connections", response_model=List[FamilyConnectionOut])
def list_family_connections(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    scopes = get_user_scopes(current_user)

    if role_name == "family_member":
        conns = session.exec(select(FamilyConnection).where(FamilyConnection.family_user_id == current_user.id)).all()
    else:
        # Facility Manager / Admin view
        if not is_sysadmin and (role_name != "facility_manager" or app_context == "CORPORATE"):
            raise HTTPException(status_code=403, detail="Not authorized to manage family connections.")
        
        stmt = select(FamilyConnection)
        if not scopes["is_system_admin"]:
            stmt = stmt.join(Resident).join(Room).join(Floor).join(Building).where(
                Building.organization_id.in_(list(scopes["organization_ids"]))
            )
        conns = session.exec(stmt).all()

    out_list = []
    for c in conns:
        res = session.get(Resident, c.resident_id)
        rm = session.get(Room, res.room_id) if res else None
        fam_user = session.get(User, c.family_user_id)
        sub = session.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == c.family_user_id)).first()

        out_list.append(FamilyConnectionOut(
            id=c.id,
            resident_id=c.resident_id,
            resident_name=f"{res.first_name} {res.last_name}" if res else "Unknown",
            room_name=rm.name if rm else "Unassigned",
            family_user_id=c.family_user_id,
            family_user_name=f"{fam_user.first_name} {fam_user.last_name}" if fam_user else "Family User",
            family_user_email=fam_user.email if fam_user else None,
            relationship=c.relationship,
            status=c.status,
            requested_at=c.requested_at,
            approved_at=c.approved_at,
            approved_by=c.approved_by,
            notes=c.notes,
            subscription_status=sub.status if sub else "PENDING",
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return out_list

def _resident_org_id(session: Session, resident_id: Optional[str]) -> Optional[str]:
    """Helper to resolve the parent organization ID of a given resident."""
    if not resident_id:
        return None
    resident = session.get(Resident, resident_id)
    room = session.get(Room, resident.room_id) if resident else None
    floor = session.get(Floor, room.floor_id) if room else None
    building = session.get(Building, floor.building_id) if floor else None
    return building.organization_id if building else None


@router.patch("/connections/{connection_id}/review", response_model=FamilyConnectionOut)
def review_family_connection(
    connection_id: str,
    review: FamilyConnectionReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    scopes = get_user_scopes(current_user)
    if not is_sysadmin and (role_name != "facility_manager" or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only elder-care facility managers and administrators can review family connection requests."
        )

    db_conn = session.get(FamilyConnection, connection_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Family connection not found.")

    if not scopes["is_system_admin"]:
        conn_org_id = _resident_org_id(session, db_conn.resident_id)
        if not conn_org_id or conn_org_id not in scopes["organization_ids"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to review family connections for another organization."
            )

    if review.status not in ["approved", "rejected", "revoked"]:
        raise HTTPException(status_code=400, detail="Status must be approved, rejected, or revoked.")

    db_conn.status = review.status
    if review.status == "approved":
        db_conn.approved_at = datetime.now(timezone.utc)
        db_conn.approved_by = current_user.id
        # Also maintain legacy user.resident_id if empty
        fam_user = session.get(User, db_conn.family_user_id)
        if fam_user and not fam_user.resident_id:
            fam_user.resident_id = db_conn.resident_id
            session.add(fam_user)
    elif review.status == "revoked":
        db_conn.revoked_at = datetime.now(timezone.utc)
        fam_user = session.get(User, db_conn.family_user_id)
        if fam_user and fam_user.resident_id == db_conn.resident_id:
            fam_user.resident_id = None
            session.add(fam_user)

    db_conn.updated_at = datetime.now(timezone.utc)
    session.add(db_conn)
    session.commit()
    session.refresh(db_conn)

    res = session.get(Resident, db_conn.resident_id)
    rm = session.get(Room, res.room_id) if res else None
    fam_user = session.get(User, db_conn.family_user_id)
    sub = session.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == db_conn.family_user_id)).first()

    return FamilyConnectionOut(
        id=db_conn.id,
        resident_id=db_conn.resident_id,
        resident_name=f"{res.first_name} {res.last_name}" if res else "Unknown",
        room_name=rm.name if rm else "Unassigned",
        family_user_id=db_conn.family_user_id,
        family_user_name=f"{fam_user.first_name} {fam_user.last_name}" if fam_user else "Family User",
        family_user_email=fam_user.email if fam_user else None,
        relationship=db_conn.relationship,
        status=db_conn.status,
        requested_at=db_conn.requested_at,
        approved_at=db_conn.approved_at,
        approved_by=db_conn.approved_by,
        notes=db_conn.notes,
        subscription_status=sub.status if sub else "PENDING",
        created_at=db_conn.created_at,
        updated_at=db_conn.updated_at
    )

# ============================================================================
# 2. FAMILY SUBSCRIPTION ARCHITECTURE (PHASE 3B)
# ============================================================================

def _staff_can_see_subscription(session: Session, current_user: User, sub: FamilySubscription) -> bool:
    scopes = get_user_scopes(current_user)
    return scopes["is_system_admin"] or subscription_org_id(session, sub) in scopes["organization_ids"]


@router.get("/subscriptions", response_model=List[FamilySubscriptionOut])
def list_family_subscriptions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if role_name == "family_member":
        subs = session.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == current_user.id)).all()
        for s_ in subs:
            lifecycle.reconcile(session, s_)
        return subs

    if not is_sysadmin and (role_name != "facility_manager" or app_context == "CORPORATE"):
        raise HTTPException(status_code=403, detail="Not authorized to inspect subscriptions.")

    visible = [s_ for s_ in session.exec(select(FamilySubscription)).all() if _staff_can_see_subscription(session, current_user, s_)]
    for s_ in visible:
        lifecycle.reconcile(session, s_)
    return visible


@router.patch("/subscriptions/{subscription_id}", response_model=FamilySubscriptionOut)
def update_family_subscription(
    subscription_id: str,
    update_in: FamilySubscriptionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Facility staff can place a hold (SUSPENDED) or lift it. They cannot mark a subscription paid: only a verified
    payment webhook does that. Staff only reach subscriptions of their own organization."""
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name != "facility_manager" or app_context == "CORPORATE"):
        raise HTTPException(status_code=403, detail="Only elder care facility managers can update subscription states.")

    sub = session.get(FamilySubscription, subscription_id)
    if not sub or not _staff_can_see_subscription(session, current_user, sub):
        raise HTTPException(status_code=404, detail="Subscription record not found.")   # same answer for other organizations
    lifecycle.reconcile(session, sub)

    target = update_in.status
    if target == "SUSPENDED":
        sub.status = "SUSPENDED"
        action = "SUBSCRIPTION_SUSPENDED_BY_STAFF"
    elif target == "ACTIVE":
        if sub.status != "SUSPENDED":
            raise HTTPException(status_code=409, detail="Staff can only lift a hold. A subscription becomes active when a payment is confirmed by the payment provider.")
        # lifting a hold restores what was paid for; it never grants time that was not paid
        if sub.end_date is None and not sub.provider_subscription_id:
            sub.status = "ACTIVE"                                      # facility-managed (legacy) subscription
        elif sub.end_date is not None and as_utc(sub.end_date) > utcnow():
            sub.status = "ACTIVE"
        else:
            sub.status = "EXPIRED"
        action = "SUBSCRIPTION_HOLD_LIFTED_BY_STAFF"
    else:
        raise HTTPException(status_code=422, detail="Staff can set status to SUSPENDED or lift a hold with ACTIVE.")
    sub.updated_at = utcnow()
    session.add(sub)
    session.commit()
    session.refresh(sub)
    record_audit_event(session, what_action=action, resource_type="SUBSCRIPTION", resource_id=sub.id,
                       who_user_id=current_user.id, who_email=current_user.email,
                       organization_id=subscription_org_id(session, sub), details={"resulting_status": sub.status})
    return sub


def emergency_block(session: Session, resident: Resident) -> dict:
    """Emergency visibility for an APPROVED family connection. Deliberately independent of the subscription: safety
    information is not a paid feature. Minimal fields only (open HIGH/CRITICAL alerts)."""
    SEV_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    alerts = session.exec(
        select(Alert).where(Alert.room_id == resident.room_id, Alert.status != "RESOLVED").order_by(Alert.created_at.desc()).limit(20)
    ).all()
    items = [{"id": a.id, "severity": a.severity, "message": a.message, "status": a.status,
              "created_at": a.created_at.isoformat() if hasattr(a.created_at, "isoformat") else str(a.created_at)}
             for a in alerts if SEV_ORDER.get(a.severity, 1) >= SEV_ORDER["HIGH"]]
    return {"available_without_subscription": True, "open_alerts": items,
            "note": "Shows open HIGH/CRITICAL alerts. Fall alerts are possible falls that need verification, not confirmed falls."}


@router.get("/emergency-status")
def get_emergency_status(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Works for any approved connection whatever the subscription status (including none, expired, suspended)."""
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if role_name != "family_member" or app_context == "CORPORATE":
        raise HTTPException(status_code=403, detail="Only family members of an elder care organization can use this.")
    conn = session.exec(select(FamilyConnection).where(FamilyConnection.family_user_id == current_user.id,
                                                       FamilyConnection.status == "approved")
                        .order_by(FamilyConnection.created_at.desc())).first()
    resident = session.get(Resident, conn.resident_id) if conn else None
    if not resident:
        raise HTTPException(status_code=403, detail="No approved connection to a resident.")
    return {"resident_id": resident.id, "resident_name": f"{resident.first_name} {resident.last_name}",
            "emergency": emergency_block(session, resident)}

# ============================================================================
# 3. FAMILY PORTAL GATED DATA + SHARING POLICY (PHASE 4)
# ============================================================================

@router.get("/resident-status")
def get_linked_resident_status(
    resident_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name != "family_member" or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resident status is only accessible by authorized family members in ELDER_CARE organizations."
        )

    # Resolve active connection
    if resident_id:
        conn = session.exec(
            select(FamilyConnection).where(
                FamilyConnection.family_user_id == current_user.id,
                FamilyConnection.resident_id == resident_id
            )
        ).first()
    else:
        conn = session.exec(
            select(FamilyConnection).where(
                FamilyConnection.family_user_id == current_user.id,
                FamilyConnection.status == "approved"
            ).order_by(FamilyConnection.created_at.desc())
        ).first()

    # Fallback to legacy AccessRequest if no FamilyConnection found
    if not conn:
        stmt_req = select(AccessRequest).where(AccessRequest.requesting_user_id == current_user.id).order_by(AccessRequest.created_at.desc())
        legacy_req = session.exec(stmt_req).first()
        if legacy_req:
            res_prof = session.get(Resident, legacy_req.resident_id)
            res_name = f"{res_prof.first_name} {res_prof.last_name}" if res_prof else "Unknown Resident"
            return {
                "linked": False,
                "connection_status": legacy_req.status,
                "subscription_status": "PENDING",
                "resident_name": res_name,
                "reason": "Connection request pending Facility Manager review."
            }
        return {
            "linked": False,
            "connection_status": None,
            "subscription_status": None,
            "reason": "No resident connection request submitted."
        }

    target_res = session.get(Resident, conn.resident_id)
    if not target_res:
        return {"linked": False, "reason": "Target resident not found."}

    # GATING 1: Connection Approval
    if conn.status != "approved":
        return {
            "linked": False,
            "connection_status": conn.status,
            "resident_id": target_res.id,
            "resident_name": f"{target_res.first_name} {target_res.last_name}",
            "reason": f"Connection is currently '{conn.status}'. Access is granted once approved by the Facility Manager."
        }

    # GATING 2: Subscription status. It only gates OPTIONAL portal features; the emergency block is always present.
    sub = session.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == current_user.id)).first()
    if sub:
        lifecycle.reconcile(session, sub)
    sub_status = sub.status if sub else "PENDING"
    room = session.get(Room, target_res.room_id)
    emergency = emergency_block(session, target_res)
    if not lifecycle.is_entitled(sub):
        return {
            "linked": True,
            "connection_status": "approved",
            "subscription_status": sub_status,
            "resident_id": target_res.id,
            "resident_name": f"{target_res.first_name} {target_res.last_name}",
            "resident": {
                "id": target_res.id,
                "first_name": target_res.first_name,
                "last_name": target_res.last_name,
                "room_name": room.name if room else "Resident Room"
            },
            "has_active_subscription": False,
            "emergency": emergency,
            "reason": f"Optional portal features need an active subscription (current status: '{sub_status}'). Emergency alerts are not affected."
        }


    # GATING 3: SharingPolicy Enforcement
    room = session.get(Room, target_res.room_id)
    floor = session.get(Floor, room.floor_id) if room else None
    building = session.get(Building, floor.building_id) if floor else None

    policy = session.exec(select(SharingPolicy).where(SharingPolicy.resident_id == target_res.id)).first()
    if not policy and building:
        policy = session.exec(select(SharingPolicy).where(SharingPolicy.organization_id == building.organization_id, SharingPolicy.resident_id == None)).first()

    share_presence = policy.share_presence if policy else True
    share_activity_detail = policy.share_activity_detail if policy else True
    share_room_name = policy.share_room_name if policy else True
    share_alert_history = policy.share_alert_history if policy else True
    severity_threshold = policy.share_alert_severity_threshold if policy else "MEDIUM"

    is_present = False
    activity = None          # unknown until a sensing event exists: never a default like "Resting"
    last_update = None
    data_source = None

    latest_event = session.exec(
        select(SensingEvent).where(SensingEvent.room_id == target_res.room_id, SensingEvent.source != "dataset").order_by(SensingEvent.timestamp.desc())
    ).first()

    if latest_event:
        act_type = session.get(ActivityType, latest_event.inferred_activity_id)
        if act_type:
            activity = act_type.name
            if activity not in ["Empty", "Unoccupied"]:
                is_present = True
        last_update = latest_event.timestamp.strftime("%H:%M:%S")
        data_source = latest_event.source
    has_data = latest_event is not None

    # Filtered recent activity history
    recent_activity_history = []
    if share_activity_detail:
        recent_events = session.exec(
            select(SensingEvent).where(SensingEvent.room_id == target_res.room_id, SensingEvent.source != "dataset").order_by(SensingEvent.timestamp.desc()).limit(5)
        ).all()
        for ev in recent_events:
            act = session.get(ActivityType, ev.inferred_activity_id)
            recent_activity_history.append({
                "timestamp": ev.timestamp.strftime("%H:%M"),
                "activity": act.name if act else "Telemetry Detected",
                "source": ev.source
            })

    # Filtered alerts according to severity threshold
    alerts_list = []
    if share_alert_history:
        SEV_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        min_sev = SEV_ORDER.get(severity_threshold, 2)
        alerts = session.exec(
            select(Alert).where(Alert.room_id == target_res.room_id).order_by(Alert.created_at.desc()).limit(5)
        ).all()
        for a in alerts:
            if SEV_ORDER.get(a.severity, 1) >= min_sev:
                alerts_list.append({
                    "id": a.id,
                    "event_type": a.event_type,
                    "severity": a.severity,
                    "message": a.message,
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if hasattr(a.created_at, "isoformat") else str(a.created_at)
                })

    return {
        "linked": True,
        "connection_status": "approved",
        "subscription_status": sub_status,
        "has_active_subscription": True,
        "emergency": emergency,
        "relationship": conn.relationship,
        "resident": {
            "id": target_res.id,
            "first_name": target_res.first_name,
            "last_name": target_res.last_name,
            "room_name": room.name if (room and share_room_name) else "Resident Suite"
        },
        # The facility's real name from the database (never a hard-coded one).
        "facility_name": (session.get(Organization, building.organization_id).name if building else None),
        # The facility's real name from the database (never a hard-coded one).
        "facility_name": (session.get(Organization, building.organization_id).name if building else None),
        # Presence is only reported when the sharing policy allows it AND a sensing event exists.
        "presence_status": ("Restricted" if not share_presence
                            else "No data" if not has_data
                            else "Present" if is_present else "Not Detected"),
        "current_activity": ("Restricted by Sharing Policy" if not share_activity_detail else activity),
        "has_data": has_data,
        "data_source": data_source,
        "last_updated": last_update,
        "recent_activity_history": recent_activity_history,
        "alerts": alerts_list,
    }

# Backward-compatibility routes for legacy access requests
@router.post("/requests", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def submit_access_request_legacy(
    req: AccessRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conn_in = FamilyConnectionCreate(resident_id=req.resident_id, relationship="Other")
    submit_family_connection(conn_in, session, current_user)
    
    db_req = AccessRequest(
        id=str(uuid.uuid4()),
        requesting_user_id=current_user.id,
        resident_id=req.resident_id,
        status="pending"
    )
    session.add(db_req)
    session.commit()
    session.refresh(db_req)
    return db_req

@router.get("/requests", response_model=List[AccessRequestOut])
def list_access_requests_legacy(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    scopes = get_user_scopes(current_user)

    if not is_sysadmin and (role_name != "facility_manager" or app_context == "CORPORATE"):
        raise HTTPException(status_code=403, detail="Not authorized to inspect family requests.")

    stmt = select(AccessRequest)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Resident, AccessRequest.resident_id == Resident.id)\
                   .join(Room, Resident.room_id == Room.id)\
                   .join(Floor, Room.floor_id == Floor.id)\
                   .join(Building, Floor.building_id == Building.id)\
                   .where(Building.organization_id.in_(list(scopes["organization_ids"])))
    return session.exec(stmt).all()

@router.patch("/requests/{request_id}", response_model=AccessRequestOut)
def review_access_request_legacy(
    request_id: str,
    review: AccessRequestReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    scopes = get_user_scopes(current_user)
    if not is_sysadmin and (role_name != "facility_manager" or app_context == "CORPORATE"):
        raise HTTPException(status_code=403, detail="Not authorized to review family requests.")

    db_req = session.get(AccessRequest, request_id)
    if not db_req:
        raise HTTPException(status_code=404, detail="Request not found.")

    if not scopes["is_system_admin"]:
        req_org_id = _resident_org_id(session, db_req.resident_id)
        if not req_org_id or req_org_id not in scopes["organization_ids"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to review family requests for another organization."
            )

    db_req.status = review.status
    db_req.reviewed_by = current_user.id
    db_req.reviewed_at = datetime.now(timezone.utc)
    db_req.updated_at = datetime.now(timezone.utc)
    session.add(db_req)
    session.commit()
    session.refresh(db_req)
    return db_req
