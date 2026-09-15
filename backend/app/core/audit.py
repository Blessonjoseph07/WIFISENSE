import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from sqlmodel import Session
from app.models.entities import AuditLog

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
    ip_address: Optional[str] = None
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
            created_at=datetime.utcnow()
        )
        session.add(log_entry)
        session.commit()
        return log_entry
    except Exception as e:
        # Don't let audit logging fail the primary transaction, but log the error
        print(f"[AuditLog Error] Failed to persist audit event: {e}")
        return None
