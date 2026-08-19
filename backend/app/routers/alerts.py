from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from app.core.database import get_session
from app.routers.auth import get_current_user
from app.models.entities import Alert, AlertAcknowledgement
from app.schemas.schemas import AlertOut, AlertResolve

router = APIRouter(prefix="/alerts", tags=["Alert Engine"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    statement = select(Alert).order_by(Alert.created_at.desc())
    return session.exec(statement).all()

@router.get("/active", response_model=List[AlertOut])
def list_active_alerts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    statement = select(Alert).where(Alert.status.in_(["new", "acknowledged"])).order_by(Alert.created_at.desc())
    return session.exec(statement).all()

@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found."
        )

    # Validate transition: only allow new -> acknowledged
    if alert.status == "acknowledged":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already acknowledged."
        )
    if alert.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved and cannot be changed."
        )
    if alert.status != "new":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from state '{alert.status}' to 'acknowledged'."
        )

    alert.status = "acknowledged"
    alert.updated_at = datetime.utcnow()
    session.add(alert)

    # Update or create AlertAcknowledgement record
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

@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: str,
    resolution_data: AlertResolve,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found."
        )

    # Validate transition: allowed states to go to resolved are new or acknowledged
    if alert.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved."
        )
    
    if alert.status not in ["new", "acknowledged"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from state '{alert.status}' to 'resolved'."
        )

    alert.status = "resolved"
    alert.updated_at = datetime.utcnow()
    session.add(alert)

    # Find or create AlertAcknowledgement to mark resolved
    ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert.id)).first()
    if not ack:
        # If it was resolved directly from 'new', create the record
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
