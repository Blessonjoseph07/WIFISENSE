from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List
from datetime import datetime
import uuid

from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes, get_user_role_and_context
from app.models.entities import User, AccessRequest, Resident, SensingEvent, ActivityType, Alert, Room, Floor, Building, Organization
from app.schemas.schemas import AccessRequestCreate, AccessRequestOut, AccessRequestReview

router = APIRouter(prefix="/family", tags=["Family Portal"])

@router.post("/requests", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def submit_access_request(
    req: AccessRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name != "emergency_contact" or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family members in elder-care organizations can submit access requests."
        )

    resident = session.get(Resident, req.resident_id)
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target resident record not found.")

    rm = session.get(Room, resident.room_id)
    flr = session.get(Floor, rm.floor_id)
    bld = session.get(Building, flr.building_id)
    org = session.get(Organization, bld.organization_id)
    if not org or org.type != "ELDER_CARE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access requests can only be made for elder-care residents.")

    existing = session.exec(
        select(AccessRequest).where(
            AccessRequest.requesting_user_id == current_user.id,
            AccessRequest.resident_id == req.resident_id,
            AccessRequest.status.in_(["pending", "org_approved", "active"])
        )
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An active or pending access request for this resident already exists.")

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
def list_access_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name not in ["organization_admin", "facility_manager"] or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only elder-care administrators and facility managers can view access requests."
        )

    scopes = get_user_scopes(current_user)
    stmt = select(AccessRequest)
    
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Resident).join(Room).join(Floor).join(Building).where(
            Building.organization_id.in_(list(scopes["organization_ids"]))
        )
    
    return session.exec(stmt).all()

@router.patch("/requests/{request_id}", response_model=AccessRequestOut)
def review_access_request(
    request_id: str,
    review: AccessRequestReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name not in ["organization_admin", "facility_manager"] or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only elder-care administrators and facility managers can review access requests."
        )
    db_req = session.get(AccessRequest, request_id)
    if not db_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found.")

    resident = session.get(Resident, db_req.resident_id)
    room = session.get(Room, resident.room_id)
    floor = session.get(Floor, room.floor_id)
    building = session.get(Building, floor.building_id)
    org_id = building.organization_id

    scopes = get_user_scopes(current_user)
    
    if review.status == "org_approved":
        if db_req.status != "pending":
            raise HTTPException(status_code=400, detail="Only pending requests can be org_approved.")
        if not scopes["is_system_admin"] and org_id not in scopes["organization_ids"]:
            raise HTTPException(status_code=403, detail="Not authorized to approve requests for this organization.")
        
    elif review.status == "active":
        if db_req.status != "org_approved":
            raise HTTPException(status_code=400, detail="Only org_approved requests can be made active.")
        if not scopes["is_system_admin"]:
            raise HTTPException(status_code=403, detail="Only system administrators can activate requests.")
            
    elif review.status == "declined":
        if db_req.status not in ["pending", "org_approved"]:
            raise HTTPException(status_code=400, detail="Cannot decline this request from its current state.")
        if not scopes["is_system_admin"] and org_id not in scopes["organization_ids"]:
            raise HTTPException(status_code=403, detail="Not authorized to decline requests for this organization.")
            
    elif review.status == "revoked":
        if db_req.status != "active":
            raise HTTPException(status_code=400, detail="Only active requests can be revoked.")
        if not scopes["is_system_admin"] and org_id not in scopes["organization_ids"]:
            raise HTTPException(status_code=403, detail="Not authorized to revoke requests for this organization.")
            
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status transition.")

    db_req.status = review.status
    db_req.reviewed_by = current_user.id
    db_req.reviewed_at = datetime.utcnow()
    db_req.updated_at = datetime.utcnow()
    session.add(db_req)

    if review.status == "active":
        target_user = session.get(User, db_req.requesting_user_id)
        if target_user:
            target_user.resident_id = db_req.resident_id
            session.add(target_user)
    elif review.status == "revoked":
        target_user = session.get(User, db_req.requesting_user_id)
        if target_user and target_user.resident_id == db_req.resident_id:
            target_user.resident_id = None
            session.add(target_user)

    session.commit()
    session.refresh(db_req)
    return db_req

@router.get("/resident-status")
def get_linked_resident_status(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (role_name != "emergency_contact" or app_context == "CORPORATE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resident status is only accessible by authorized emergency contacts in ELDER_CARE organizations."
        )

    if not current_user.resident_id:
        stmt_req = select(AccessRequest).where(AccessRequest.requesting_user_id == current_user.id).order_by(AccessRequest.created_at.desc())
        req = session.exec(stmt_req).first()
        if req:
            resident_profile = session.get(Resident, req.resident_id)
            res_name = f"{resident_profile.first_name} {resident_profile.last_name}" if resident_profile else "Unknown Resident"
            return {
                "linked": False,
                "request_status": req.status,
                "resident_name": res_name
            }
        return {
            "linked": False,
            "request_status": None
        }

    from app.models.entities import SharingPolicy

    resident = session.get(Resident, current_user.resident_id)
    if not resident:
        return {"linked": False, "request_status": None}

    room = session.get(Room, resident.room_id)
    floor = session.get(Floor, room.floor_id)
    building = session.get(Building, floor.building_id)

    # Fetch Policy (resident override or org default)
    policy_stmt = select(SharingPolicy).where(SharingPolicy.resident_id == resident.id)
    policy = session.exec(policy_stmt).first()
    if not policy:
        policy_stmt = select(SharingPolicy).where(SharingPolicy.organization_id == building.organization_id, SharingPolicy.resident_id == None)
        policy = session.exec(policy_stmt).first()
    
    # Fallback default policy if none exists
    share_presence = policy.share_presence if policy else True
    share_activity_detail = policy.share_activity_detail if policy else True
    share_room_name = policy.share_room_name if policy else True
    share_alert_history = policy.share_alert_history if policy else True

    is_present = False
    activity = "Empty"
    last_update = None

    if share_presence or share_activity_detail:
        stmt = select(SensingEvent).where(SensingEvent.room_id == resident.room_id).order_by(SensingEvent.timestamp.desc())
        latest_event = session.exec(stmt).first()

        if latest_event:
            act_type = session.get(ActivityType, latest_event.inferred_activity_id)
            if act_type:
                activity = act_type.name
                if activity != "Empty":
                    is_present = True
            last_update = latest_event.timestamp.isoformat()

    alerts_list = []
    if share_alert_history:
        alerts = session.exec(select(Alert).where(Alert.room_id == resident.room_id).order_by(Alert.created_at.desc())).all()
        for a in alerts:
            alerts_list.append({
                "id": a.id,
                "event_type": a.event_type,
                "severity": a.severity,
                "message": a.message,
                "status": a.status,
                "created_at": a.created_at.isoformat()
            })

    return {
        "linked": True,
        "request_status": "active",
        "resident": {
            "id": resident.id,
            "first_name": resident.first_name,
            "last_name": resident.last_name,
            "room_name": room.name if room and share_room_name else "Restricted View"
        },
        "presence_status": "present" if is_present else "not detected" if share_presence else "restricted",
        "recent_activity": {
            "activity": activity if share_activity_detail else "Restricted View",
            "timestamp": last_update if (share_presence or share_activity_detail) else None
        },
        "alerts": alerts_list,
        "facility_contact": {
            "name": "Care Desk",
            "phone": "+91 4828 251122",
            "email": "caredesk@wifisense.com"
        }
    }
