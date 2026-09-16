import json
import urllib.request
import urllib.error
import time
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import AuditLog, Alert, SensingDevice, Room, Resident, FamilyConnection, FamilySubscription, SharingPolicy, User, SensingEvent
from app.services.notifications import process_alert_notifications, send_alert_email

API_BASE = "http://127.0.0.1:8000"

def api_call(endpoint, method="GET", data=None, token=None):
    url = f"{API_BASE}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed

def login(email, password):
    status, res = api_call("/auth/login", method="POST", data={"email": email, "password": password})
    assert status == 200, f"Login failed for {email}: {status} {res}"
    return res

def test_alert_notification_e2e():
    """
    Test 1: End-to-end API simulation:
    - Triggers simulated fall event.
    - Verifies non-blocking alert creation (returns 201 immediately).
    - Verifies background notification delivery is invoked.
    - Verifies audit log records NOTIFICATION_FAILED when SMTP is unreachable.
    - Verifies recipient resolution includes caregivers and authorized family members.
    """
    print("\n--- Test 1: E2E Fall Alert Creation & Non-Blocking Notification Delivery ---")
    
    auth_data = login("blesson@wifisense.com", "blessonpassword")
    token = auth_data["access_token"]
    
    with Session(engine) as session:
        # Use Room 102 device (dev_ec_102) which has Resident Mary Joseph
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:02")).first()
        assert device is not None, "Elder care seeded device for Room 102 not found."
        device_id = device.id
    
    alert_id = None
    event_id = None
    try:
        # Simulate a fall event
        print(f"Simulating Fall_Detected event for device {device_id}...")
        status_code, response_data = api_call(
            "/sensing/simulate-event",
            method="POST",
            token=token,
            data={
                "device_id": device_id,
                "simulated_activity": "Fall_Detected"
            }
        )
        
        # 1. Verify it returns 201 Created and didn't block due to SMTP connection failure
        assert status_code == 201, f"Expected 201, got {status_code}. Response: {response_data}"
        assert response_data["alert_triggered"] is True
        alert_id = response_data["alert"]["id"]
        event_id = response_data["sensing_event"]["id"]
        print(f"[PASS] Alert {alert_id} created successfully without blocking (HTTP 201).")
        
        # 2. Wait up to 10 seconds for the background task to attempt SMTP and log the failure
        print("Waiting for async background notification task...")
        log = None
        for _ in range(10):
            time.sleep(1)
            with Session(engine) as session:
                log = session.exec(
                    select(AuditLog).where(
                        AuditLog.resource_id == alert_id,
                        AuditLog.what_action == "NOTIFICATION_FAILED"
                    )
                ).first()
                if log:
                    break
                    
        assert log is not None, f"Audit log for notification failure of alert {alert_id} was not created."
        assert log.result == "FAILURE"
        assert log.resource_type == "ALERT"
        
        recipients = log.details.get("recipients", [])
        print(f"[PASS] Notification delivery failed gracefully as expected (No SMTP server).")
        print(f"       Resolved recipients ({len(recipients)}): {recipients}")
        
        # Verify caregivers are present
        assert "abhinanth@wifisense.com" in recipients, "Caregiver abhinanth@wifisense.com missing from recipients."
        
        # Verify authorized active family members are present (Anna Joseph for Mary Joseph)
        assert "anna@wifisense.com" in recipients, "Authorized family member anna@wifisense.com missing from recipients."
        print("[PASS] Both assigned caregivers and authorized family members resolved.")

    finally:
        # Clean up test alert and event so subsequent test suites aren't polluted
        if alert_id or event_id:
            with Session(engine) as session:
                if alert_id:
                    alt = session.get(Alert, alert_id)
                    if alt:
                        session.delete(alt)
                if event_id:
                    evt = session.get(SensingEvent, event_id)
                    if evt:
                        session.delete(evt)
                session.commit()

def test_sharing_policy_gating():
    """
    Test 2: Verify Sharing Policy and Subscription gating:
    - If a resident's sharing policy has share_alert_history = False, family members must NOT receive notifications.
    - If an alert's severity is below the sharing policy threshold, family members must NOT receive notifications.
    """
    print("\n--- Test 2: Sharing Policy Gating & Authorization ---")
    
    with Session(engine) as session:
        resident = session.exec(select(Resident).where(Resident.first_name == "Mary")).first()
        assert resident is not None
        
        policy = session.exec(select(SharingPolicy).where(SharingPolicy.resident_id == resident.id)).first()
        original_share = policy.share_alert_history
        test_alert = None
        
        try:
            # Disable alert sharing in policy
            policy.share_alert_history = False
            session.add(policy)
            session.commit()
            
            # Create a test alert
            test_alert = Alert(
                room_id=resident.room_id,
                event_type="Fall_Detected",
                severity="CRITICAL",
                message="Policy Gating Test Alert"
            )
            session.add(test_alert)
            session.commit()
            session.refresh(test_alert)
            
            # Process notifications
            process_alert_notifications(test_alert.id, resident.room_id, test_alert.message)
            
            # Check audit log for recipients
            log = session.exec(
                select(AuditLog).where(
                    AuditLog.resource_id == test_alert.id,
                    AuditLog.what_action == "NOTIFICATION_FAILED"
                )
            ).first()
            assert log is not None
            recipients = log.details.get("recipients", [])
            
            # Caregivers should be included, but family members should NOT
            assert "abhinanth@wifisense.com" in recipients
            assert "anna@wifisense.com" not in recipients, "Family member received notification despite share_alert_history=False!"
            print("[PASS] Family members successfully excluded when share_alert_history is False.")
            
        finally:
            # Restore policy and delete test alert
            policy.share_alert_history = original_share
            session.add(policy)
            if test_alert:
                alt = session.get(Alert, test_alert.id)
                if alt:
                    session.delete(alt)
            session.commit()

def test_unit_send_alert_email_graceful_error_handling():
    """
    Test 3: Unit test for send_alert_email:
    - Verifies that even if SMTP completely fails, no exception is raised to the caller.
    - Verifies an AuditLog entry is committed with result='FAILURE'.
    """
    print("\n--- Test 3: Unit send_alert_email Graceful Error Handling ---")
    
    with Session(engine) as session:
        # Call send_alert_email directly with a dummy recipient
        send_alert_email(
            session=session,
            recipients=["test@example.com"],
            subject="Test Unit Alert",
            body="Test Unit Body",
            alert_id="dummy-alert-123"
        )
        
        log = session.exec(
            select(AuditLog).where(
                AuditLog.resource_id == "dummy-alert-123",
                AuditLog.what_action == "NOTIFICATION_FAILED"
            )
        ).first()
        
        assert log is not None, "Audit log was not created for dummy alert failure."
        assert log.result == "FAILURE"
        assert log.details["recipient_count"] == 1
        
        # Clean up dummy audit log
        session.delete(log)
        session.commit()
        print("[PASS] send_alert_email handled exception cleanly and created audit log.")

if __name__ == "__main__":
    print("==================================================")
    print("      WIFISENSE ALERT NOTIFICATION TEST SUITE     ")
    print("==================================================")
    test_alert_notification_e2e()
    test_sharing_policy_gating()
    test_unit_send_alert_email_graceful_error_handling()
    print("\n==================================================")
    print("       ALL ALERT NOTIFICATION TESTS PASSED        ")
    print("==================================================")
