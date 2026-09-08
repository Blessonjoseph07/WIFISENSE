from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List
from datetime import datetime
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import Alert, AlertAcknowledgement, Room, Floor, Building
from app.schemas.schemas import AlertOut, AlertResolve

router = APIRouter(prefix="/alerts", tags=["Alert Engine"])
STAFF_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver", "corporate_staff"]

def get_scoped_alert_query(scopes):
    stmt = select(Alert)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Room).join(Floor).join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))
    return stmt

@router.get("", response_model=List[AlertOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_alerts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).order_by(Alert.created_at.desc())
    return session.exec(stmt).all()

@router.get("/active", response_model=List[AlertOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_active_alerts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = get_scoped_alert_query(scopes).where(Alert.status.in_(["new", "acknowledged"])).order_by(Alert.created_at.desc())
    return session.exec(stmt).all()

@router.patch("/{alert_id}/acknowledge", response_model=AlertOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is already acknowledged.")
    if alert.status == "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is already resolved and cannot be changed.")
    if alert.status != "new":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid transition from state '{alert.status}' to 'acknowledged'.")

    alert.status = "acknowledged"
    alert.updated_at = datetime.utcnow()
    session.add(alert)

    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    if not ack:
        ack = AlertAcknowledgement(
            alert_id=alert.id,
            user_id=current_user.id,
            acknowledged_at=datetime.utcnow()
        )
    else:
        ack.user_id = current_user.id
        ack.acknowledged_at = datetime.utcnow()
    session.add(ack)
    
    session.commit()
    session.refresh(alert)
    return alert

@router.patch("/{alert_id}/resolve", response_model=AlertOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is already resolved.")
    if alert.status not in ["new", "acknowledged"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid transition from state '{alert.status}' to 'resolved'.")

    alert.status = "resolved"
    alert.updated_at = datetime.utcnow()
    session.add(alert)

    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    if not ack:
        ack = AlertAcknowledgement(
            alert_id=alert.id,
            user_id=current_user.id,
            acknowledged_at=datetime.utcnow(),
            resolved_at=datetime.utcnow(),
            resolution_notes=resolution_data.resolution_notes
        )
    else:
        ack.resolved_at = datetime.utcnow()
        ack.resolution_notes = resolution_data.resolution_notes
    session.add(ack)

    session.commit()
    session.refresh(alert)
    return alert
