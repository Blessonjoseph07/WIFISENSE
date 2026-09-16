import smtplib
import logging
from email.message import EmailMessage
from sqlmodel import Session, select, or_
from app.core.config import settings
from app.core.audit import record_audit_event
from typing import List, Optional

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

def send_alert_email(
    session: Session,
    recipients: List[str],
    subject: str,
    body: str,
    alert_id: str,
    html_body: Optional[str] = None
) -> None:
    """
    Sends an alert email to a list of recipients via standard library smtplib.
    Logs an audit event if the delivery fails, allowing the alert to proceed gracefully.
    """
    if not recipients:
        return

    msg = EmailMessage()
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Alert email sent successfully to {len(recipients)} recipients for alert {alert_id}")
    except Exception as e:
        error_msg = f"Failed to send alert email: {str(e)}"
        logger.error(error_msg)
        
        # Log delivery failure gracefully via audit infrastructure
        record_audit_event(
            session=session,
            what_action="NOTIFICATION_FAILED",
            resource_type="ALERT",
            resource_id=alert_id,
            result="FAILURE",
            who_user_id="system",
            who_email="system@wifisense.com",
            details={
                "error": error_msg,
                "recipients": recipients,
                "recipient_count": len(recipients)
            }
        )
        # Commit the audit event since we might be inside a background task
        try:
            session.commit()
        except Exception as commit_err:
            logger.error(f"Failed to commit audit event for notification failure: {commit_err}")

def process_alert_notifications(
    alert_id: str,
    room_id: str,
    alert_msg: str
) -> None:
    """
    Background task entry point for processing alert notifications.
    Creates a new DB session, resolves recipients (caregivers and authorized active family members),
    and sends the email notification.
    """
    from app.core.database import engine
    from app.models.entities import (
        User, Role, UserRole, Resident, EmergencyContact, 
        FamilyConnection, FamilySubscription, SharingPolicy, Organization, Building, Floor, Room, Alert
    )

    with Session(engine) as session:
        recipients: List[str] = []
        
        alert = session.get(Alert, alert_id)
        severity = alert.severity.upper() if alert and alert.severity else "CRITICAL"
        alert_timestamp = alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if alert else "Just now"

        room = session.get(Room, room_id)
        if not room:
            return
            
        floor = session.get(Floor, room.floor_id)
        building = session.get(Building, floor.building_id) if floor else None
        org = session.get(Organization, building.organization_id) if building else None
        
        # 1. Caregivers assigned to room, building, or organization
        stmt = (
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                Role.name == "caregiver",
                User.is_active == True,
                or_(
                    UserRole.organization_id == org.id if org else False,
                    UserRole.building_id == building.id if building else False,
                    UserRole.room_id == room.id
                )
            )
        )
        caregivers = session.exec(stmt).all()
        for caregiver in caregivers:
            if caregiver.email and caregiver.email not in recipients:
                recipients.append(caregiver.email)
                
        # 2. Family Members & Emergency Contacts
        resident = session.exec(select(Resident).where(Resident.room_id == room.id)).first()
        primary_contact = None
        
        if resident:
            contacts = session.exec(
                select(EmergencyContact)
                .where(EmergencyContact.resident_id == resident.id)
                .order_by(EmergencyContact.priority)
            ).all()
            if contacts:
                primary_contact = contacts[0]
                
            # Check Sharing Policy
            policy = session.exec(
                select(SharingPolicy).where(SharingPolicy.resident_id == resident.id)
            ).first()
            if not policy and org:
                policy = session.exec(
                    select(SharingPolicy).where(
                        SharingPolicy.organization_id == org.id,
                        SharingPolicy.resident_id == None
                    )
                ).first()
                
            # Check if policy allows alerts and meets severity threshold
            policy_threshold = policy.share_alert_severity_threshold.upper() if policy else "MEDIUM"
            alert_sev_level = SEVERITY_ORDER.get(severity, 4)
            thresh_level = SEVERITY_ORDER.get(policy_threshold, 2)
            
            can_share_alerts = (policy is not None and policy.share_alert_history and alert_sev_level >= thresh_level)

            if can_share_alerts:
                connections = session.exec(
                    select(FamilyConnection)
                    .where(FamilyConnection.resident_id == resident.id, FamilyConnection.status == "approved")
                ).all()
                
                for conn in connections:
                    sub = session.exec(
                        select(FamilySubscription)
                        .where(
                            or_(
                                FamilySubscription.family_connection_id == conn.id,
                                FamilySubscription.family_user_id == conn.family_user_id
                            )
                        )
                    ).first()
                    if sub and sub.status in ["ACTIVE", "CARE_MONTHLY"]:
                        family_user = session.get(User, conn.family_user_id)
                        if family_user and family_user.is_active and family_user.email not in recipients:
                            recipients.append(family_user.email)

        if not recipients:
            logger.info(f"No recipients resolved for alert {alert_id} in room {room.name}")
            return
            
        resident_name = f"{resident.first_name} {resident.last_name}" if resident else "Unassigned / Unknown"
        dashboard_url = f"{settings.FRONTEND_URL}/caregiver"

        subject = f"[{severity}] WIFISENSE ALERT: {alert_msg}"
        
        # Plain text formatting
        body_lines = [
            f"WIFISENSE ALERT NOTIFICATION",
            f"=============================",
            f"Severity:  {severity}",
            f"Alert:     {alert_msg}",
            f"Timestamp: {alert_timestamp}",
            f"Location:  Room {room.name}",
            f"Resident:  {resident_name}",
            ""
        ]
        if primary_contact:
            body_lines.extend([
                f"Emergency Contact:",
                f"  Name:         {primary_contact.name}",
                f"  Phone:        {primary_contact.phone}",
                f"  Relationship: {primary_contact.relationship}",
                ""
            ])
        body_lines.append(f"Open Dashboard: {dashboard_url}\n")
        body = "\n".join(body_lines)

        # Clean minimal HTML formatting
        html_contact = ""
        if primary_contact:
            html_contact = f"""
            <div style="margin-top: 15px; padding: 12px; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 6px;">
                <strong style="color: #856404;">Primary Emergency Contact:</strong><br/>
                Name: {primary_contact.name}<br/>
                Phone: <a href="tel:{primary_contact.phone}">{primary_contact.phone}</a><br/>
                Relationship: {primary_contact.relationship}
            </div>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-left: 4px solid #dc3545; padding-left: 15px; margin-bottom: 20px;">
                <h2 style="color: #dc3545; margin: 0;">WiFiSense Safety Alert: {severity}</h2>
                <p style="margin: 5px 0 0; font-size: 1.1em; font-weight: bold;">{alert_msg}</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr><td style="padding: 6px 0; color: #666; width: 120px;">Location:</td><td><strong>Room {room.name}</strong></td></tr>
                <tr><td style="padding: 6px 0; color: #666;">Resident:</td><td><strong>{resident_name}</strong></td></tr>
                <tr><td style="padding: 6px 0; color: #666;">Timestamp:</td><td>{alert_timestamp}</td></tr>
            </table>
            {html_contact}
            <div style="margin-top: 25px;">
                <a href="{dashboard_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Open Caregiver Dashboard</a>
            </div>
            <p style="margin-top: 30px; font-size: 0.85em; color: #999;">This is an automated safety alert notification from WiFiSense.</p>
        </body>
        </html>
        """

        send_alert_email(session, recipients, subject, body, alert_id, html_body=html_body)
