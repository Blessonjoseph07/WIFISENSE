from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime
import uuid

from app.core.database import get_session
from app.routers.auth import get_current_user
from app.models.entities import User, AccessRequest, Resident, SensingEvent, ActivityType, Alert, Room
from app.schemas.schemas import AccessRequestCreate, AccessRequestOut, AccessRequestReview

router = APIRouter(prefix="/family", tags=["Family Portal"])

@router.post("/requests", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def submit_access_request(
    req: AccessRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify target resident exists
    resident = session.get(Resident, req.resident_id)
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target resident record not found."
        )

    # Check if there is already a pending or approved request for this user and resident
    existing = session.exec(
        select(AccessRequest).where(
            AccessRequest.requesting_user_id == current_user.id,
            AccessRequest.resident_id == req.resident_id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An access request for this resident already exists."
        )

    # Create new access request
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
    # System Admin (role_id 1) or Organization Admin (role_id 2)
    # Check current_user's roles
    user_roles = [r.role_id for r in current_user.roles]
    if 1 not in user_roles and 2 not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrators only."
        )
    
    return session.exec(select(AccessRequest)).all()

@router.patch("/requests/{request_id}", response_model=AccessRequestOut)
def review_access_request(
    request_id: str,
    review: AccessRequestReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role_id for r in current_user.roles]
    if 1 not in user_roles and 2 not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrators only."
        )

    db_req = session.get(AccessRequest, request_id)
    if not db_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access request not found."
        )

    if review.status not in ["approved", "declined"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'approved' or 'declined'."
        )

    db_req.status = review.status
    db_req.reviewed_by = current_user.id
    db_req.reviewed_at = datetime.utcnow()
    db_req.updated_at = datetime.utcnow()
    session.add(db_req)

    if review.status == "approved":
        # Link resident to target requesting user
        target_user = session.get(User, db_req.requesting_user_id)
        if target_user:
            target_user.resident_id = db_req.resident_id
            session.add(target_user)

    session.commit()
    session.refresh(db_req)
    return db_req

@router.get("/resident-status")
def get_linked_resident_status(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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

    resident = session.get(Resident, current_user.resident_id)
    if not resident:
        return {
            "linked": False,
            "request_status": None
        }

    room = session.get(Room, resident.room_id)
    
    # Query latest activity event
    stmt = select(SensingEvent).where(SensingEvent.room_id == resident.room_id).order_by(SensingEvent.timestamp.desc())
    latest_event = session.exec(stmt).first()

    is_present = False
    activity = "Empty"
    last_update = None

    if latest_event:
        act_type = session.get(ActivityType, latest_event.inferred_activity_id)
        if act_type:
            activity = act_type.name
            if activity != "Empty":
                is_present = True
        last_update = latest_event.timestamp.isoformat()

    # Query alert history (read-only, THAT resident/room only)
    alerts = session.exec(
        select(Alert).where(Alert.room_id == resident.room_id).order_by(Alert.created_at.desc())
    ).all()

    return {
        "linked": True,
        "request_status": "approved",
        "resident": {
            "id": resident.id,
            "first_name": resident.first_name,
            "last_name": resident.last_name,
            "room_name": room.name if room else "Unknown Room"
        },
        "presence_status": "present" if is_present else "not detected",
        "recent_activity": {
            "activity": activity,
            "timestamp": last_update
        },
        "alerts": [
            {
                "id": a.id,
                "event_type": a.event_type,
                "severity": a.severity,
                "message": a.message,
                "status": a.status,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ],
        "facility_contact": {
            "name": "WiFi Sense Research Lab Care Desk",
            "phone": "+91 4828 251122",
            "email": "caredesk@wifisense.com"
        }
    }
