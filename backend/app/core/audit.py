import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import Request
from sqlmodel import Session, select
from app.models.entities import AuditLog, DoctorProfile, User, UserRole


def resolve_organization(
    session: Session,
    who_user_id: Optional[str],
    who_email: Optional[str],
    details: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Which organization does this event belong to? Actor first, then what the caller recorded.

    The actor's own organization wins on purpose: a denied attempt by a user of organization A to touch organization B's
    data belongs to A's trail, not B's. Returns None when no single organization can be named."""
    user_id = who_user_id
    if not user_id and who_email:
        user = session.exec(select(User).where(User.email == who_email)).first()
        user_id = user.id if user else None
    if user_id:
        orgs = {r.organization_id for r in session.exec(select(UserRole).where(UserRole.user_id == user_id)).all()
                if r.organization_id}
        if len(orgs) == 1:
            return next(iter(orgs))
        if not orgs:
            profile = session.exec(select(DoctorProfile).where(DoctorProfile.user_id == user_id)).first()
            if profile:
                return profile.organization_id
    org = (details or {}).get("organization_id") if isinstance(details, dict) else None
    return org if isinstance(org, str) and org else None

def record_audit_event(
    session: Session,
    what_action: str,
    resource_type: str,
    result: str = "SUCCESS",
    who_user_id: Optional[str] = None,
    who_email: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    ip_address: Optional[str] = None,
    organization_id: Optional[str] = None
) -> Optional[AuditLog]:
    """
    Creates and persists a structured audit log event answering:
    WHO, WHAT, WHEN, RESOURCE, RESULT.
    """
    try:
        resolved_ip = ip_address
        if not resolved_ip and request:
            if request.client and request.client.host:
                resolved_ip = request.client.host
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                resolved_ip = forwarded.split(",")[0].strip()

        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            who_user_id=who_user_id,
            who_email=who_email,
            what_action=what_action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            details=details,
            ip_address=resolved_ip,
            organization_id=organization_id or resolve_organization(session, who_user_id, who_email, details),
            created_at=datetime.now(timezone.utc)
        )
        session.add(log_entry)
        session.commit()
        return log_entry
    except Exception as e:
        # Don't let audit logging fail the primary transaction, but log the error
        print(f"[AuditLog Error] Failed to persist audit event: {e}")
        return None
