"""
WIFISENSE BUSINESS LOGIC & SENSING TELEMETRY TEST SUITE (ITEM 3)
================================================================
This suite verifies critical application behaviors beyond authentication and scoping boundaries:

1. Sensing Event Pipeline & Classification:
   - simulate-event creates a SensingEvent with correct classification profile,
     RF features, confidence, and links it accurately to room and device.

2. Alert Lifecycle & Actor Attribution:
   - Creation -> Acknowledgment -> Resolution lifecycle.
   - AlertAcknowledgement table correctly attributes acting user (caregiver) and timestamps.
   - Invalid lifecycle state transitions (e.g. acknowledging already resolved alert) are rejected.

3. Analytics "Not Enough Data" Truth in Telemetry:
   - Verifies that querying analytics for a fresh/empty organization returns the honest
     "no data / zero metrics" state (total_rooms=0, occupancy_rate=0.0, total_alerts=0),
     rather than fabricated or placeholder numbers.

4. Profile Photo Security & Magic-Byte Anti-Disguise Pipeline:
   - Verifies that file extension masquerading (e.g. non-image payload renamed .png)
     is strictly detected and rejected via magic-byte sniffing.
   - Verifies that corrupt headers with valid magic bytes are rejected via Pillow verification.
   - Verifies that a valid real image is processed and accepted.
"""

import os
import io
import json
import urllib.request
import urllib.error
import uuid
import time
from pathlib import Path
from PIL import Image
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import (
    User, Role, UserRole, Organization, Building, Floor, Room,
    SensingDevice, SensingEvent, ActivityType, Alert, AlertAcknowledgement, AuditLog
)

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# Test credentials with configurable fallbacks to seeded development users
SYSADMIN_EMAIL = os.getenv("TEST_SYSADMIN_EMAIL", "blesson@wifisense.com")
SYSADMIN_PASSWORD = os.getenv("TEST_SYSADMIN_PASSWORD", "blessonpassword")

CAREGIVER_EMAIL = os.getenv("TEST_CAREGIVER_EMAIL", "abhinanth@wifisense.com")
CAREGIVER_PASSWORD = os.getenv("TEST_CAREGIVER_PASSWORD", "abhinanthpassword")

def generate_valid_png():
    """Dynamically generates valid PNG image binary bytes using Pillow."""
    img = Image.new("RGB", (10, 10), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

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

def upload_multipart(endpoint, field_name, filename, file_bytes, content_type, token=None):
    url = f"{API_BASE}{endpoint}"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        f"\r\n--{boundary}--\r\n".encode("utf-8")
    ]
    body = b"".join(parts)
    
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        
    try:
        with urllib.request.urlopen(req) as resp:
            body_text = resp.read().decode("utf-8")
            return resp.status, json.loads(body_text) if body_text else None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8")
        try:
            parsed = json.loads(body_text)
        except Exception:
            parsed = body_text
        return e.code, parsed

def login(email, password):
    status, res = api_call("/auth/login", method="POST", data={"email": email, "password": password})
    assert status == 200, f"Login failed for {email}: {status} {res}"
    return res

# ============================================================================
# 1. SENSING EVENT PIPELINE & CLASSIFICATION
# ============================================================================
def test_sensing_event_creation_and_classification():
    """
    Verifies simulate-event creates a SensingEvent with correct classification,
    extracted features, model confidence, and proper device/room links.
    """
    print("\n--- 1. Testing Sensing Event Pipeline & Classification ---")
    
    auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = auth["access_token"]
    
    # Locate a seeded sensing device (e.g. dev_ec_101)
    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        assert device is not None, "Seeded sensing device not found."
        device_id = device.id
        room_id = device.room_id
        assert room_id is not None, "Test device must be assigned to a room."

    simulated_activity = "Walking"
    status, res = api_call(
        "/sensing/simulate-event",
        method="POST",
        token=token,
        data={
            "device_id": device_id,
            "simulated_activity": simulated_activity
        }
    )
    assert status == 201, f"Expected 201, got {status}: {res}"
    assert res["presence_detected"] is True
    assert res["activity_classified"] == simulated_activity
    assert res["alert_triggered"] is False
    
    event_data = res["sensing_event"]
    event_id = event_data["id"]
    assert event_data["device_id"] == device_id
    assert event_data["room_id"] == room_id
    assert event_data["event_type"] == "MotionDetected"
    assert event_data["confidence"] > 0.85
    
    features = event_data["extracted_features"]
    assert "doppler_shift_hz" in features and features["doppler_shift_hz"] > 0
    assert "variance_amplitude" in features and features["variance_amplitude"] > 0
    
    # Direct database verification
    with Session(engine) as session:
        db_event = session.get(SensingEvent, event_id)
        assert db_event is not None, "SensingEvent was not saved in DB."
        assert db_event.device_id == device_id
        assert db_event.room_id == room_id
        
        act = session.get(ActivityType, db_event.inferred_activity_id)
        assert act is not None and act.name == simulated_activity
        print(f"[PASS] SensingEvent #{event_id} verified in DB (Activity: {act.name}, Confidence: {db_event.model_confidence}).")
        
        # Clean up test event so seed data remains clean
        session.delete(db_event)
        session.commit()
        print("[PASS] Cleaned up test SensingEvent.")

# ============================================================================
# 2. ALERT LIFECYCLE & ACTOR ATTRIBUTION
# ============================================================================
def test_alert_lifecycle_and_actor_attribution():
    """
    Verifies full Alert lifecycle:
    Creation (Fall_Detected) -> Acknowledgment (Caregiver) -> Resolution (Caregiver).
    Verifies AlertAcknowledgement attributes the acting user and timestamps.
    Verifies invalid lifecycle transitions are rejected.
    """
    print("\n--- 2. Testing Alert Lifecycle & AlertAcknowledgement Attribution ---")
    
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    cg_auth = login(CAREGIVER_EMAIL, CAREGIVER_PASSWORD)
    cg_token = cg_auth["access_token"]
    cg_user_id = cg_auth["user"]["id"]
    
    # 1. Trigger simulated Fall_Detected event to create Alert
    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        device_id = device.id
        
    status, sim_res = api_call(
        "/sensing/simulate-event",
        method="POST",
        token=sys_auth["access_token"],
        data={
            "device_id": device_id,
            "simulated_activity": "Fall_Detected"
        }
    )
    assert status == 201
    assert sim_res["alert_triggered"] is True
    alert_info = sim_res["alert"]
    alert_id = alert_info["id"]
    event_id = sim_res["sensing_event"]["id"]
    print(f"[PASS] Fall alert created: {alert_id} (Status: {alert_info['status']})")
    
    try:
        # Verify initial DB state
        with Session(engine) as session:
            db_alert = session.get(Alert, alert_id)
            assert db_alert is not None
            assert db_alert.status == "new"
            assert db_alert.severity == "CRITICAL"
            
            # Initial AlertAcknowledgement should not exist yet
            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is None
        
        # 2. Acknowledge Alert as Caregiver
        status, ack_res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=cg_token)
        assert status == 200, f"Expected 200, got {status}: {ack_res}"
        assert ack_res["status"] == "acknowledged"
        print(f"[PASS] Caregiver acknowledged alert {alert_id}.")
        
        # Verify AlertAcknowledgement in DB
        with Session(engine) as session:
            db_alert = session.get(Alert, alert_id)
            assert db_alert.status == "acknowledged"
            
            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is not None, "AlertAcknowledgement record was not created."
            assert ack.user_id == cg_user_id, f"Expected acting user {cg_user_id}, got {ack.user_id}"
            assert ack.acknowledged_at is not None
            assert ack.resolved_at is None
            print(f"[PASS] AlertAcknowledgement recorded: acting user {ack.user_id} at {ack.acknowledged_at}.")
            
            # Verify AuditLog recorded ALERT_ACKNOWLEDGED
            audit = session.exec(
                select(AuditLog).where(
                    AuditLog.resource_id == alert_id,
                    AuditLog.what_action == "ALERT_ACKNOWLEDGED"
                )
            ).first()
            assert audit is not None
            assert audit.who_user_id == cg_user_id
            print(f"[PASS] Audit log verified: {audit.what_action} by {audit.who_email}.")

        # 3. Resolve Alert as Caregiver
        notes = "Resident checked. Verified safe and assisted into chair."
        status, res_res = api_call(
            f"/alerts/{alert_id}/resolve",
            method="PATCH",
            token=cg_token,
            data={"resolution_notes": notes}
        )
        assert status == 200, f"Expected 200, got {status}: {res_res}"
        assert res_res["status"] == "resolved"
        print(f"[PASS] Caregiver resolved alert {alert_id}.")
        
        # Verify AlertAcknowledgement resolution state
        with Session(engine) as session:
            db_alert = session.get(Alert, alert_id)
            assert db_alert.status == "resolved"
            
            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is not None
            assert ack.resolved_at is not None
            assert ack.resolution_notes == notes
            print(f"[PASS] AlertAcknowledgement resolved_at ({ack.resolved_at}) and notes verified.")

        # 4. Attempt Invalid Transition: Cannot re-acknowledge an already resolved alert
        status, err_res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=cg_token)
        assert status == 400, f"Expected 400 when acknowledging resolved alert, got {status}: {err_res}"
        print("[PASS] Re-acknowledging already resolved alert correctly rejected with HTTP 400.")

    finally:
        # Clean up test alert, ack, and event
        with Session(engine) as session:
            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            if ack:
                session.delete(ack)
            alt = session.get(Alert, alert_id)
            if alt:
                session.delete(alt)
            evt = session.get(SensingEvent, event_id)
            if evt:
                session.delete(evt)
            session.commit()
        print("[PASS] Cleaned up lifecycle test alert and acknowledgements.")

# ============================================================================
# 3. ANALYTICS "NOT ENOUGH DATA" STATE (ZERO FABRICATED METRICS)
# ============================================================================
def test_analytics_empty_organization_unfabricated_data():
    """
    Verifies that querying analytics for a fresh/empty organization returns
    an honest 'not enough data' zero state rather than fabricated or placeholder numbers.
    """
    print("\n--- 3. Testing Analytics 'Not Enough Data' for Empty Organization ---")
    
    from app.core.security import hash_password
    
    empty_org_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    test_email = f"empty_admin_{uuid.uuid4().hex[:6]}@wifisense.com"
    test_password = "Password123!"
    
    with Session(engine) as session:
        # Create an empty test organization
        empty_org = Organization(
            id=empty_org_id,
            name="Empty Test Facility",
            type="ELDER_CARE"
        )
        session.add(empty_org)
        
        # Create user assigned solely to this empty organization
        test_user = User(
            id=test_user_id,
            email=test_email,
            password_hash=hash_password(test_password),
            first_name="Empty",
            last_name="Admin",
            is_active=True
        )
        session.add(test_user)
        session.commit()
        
        # Assign organization_admin role scoped to empty_org
        ur = UserRole(
            user_id=test_user_id,
            role_id=2,  # organization_admin
            organization_id=empty_org_id
        )
        session.add(ur)
        session.commit()
        
    try:
        # Login as the empty org admin
        auth = login(test_email, test_password)
        token = auth["access_token"]
        
        # 1. Test /analytics/occupancy-summary
        status, occ = api_call("/analytics/occupancy-summary", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {occ}"
        assert occ["total_rooms"] == 0, f"Expected 0 total rooms, got {occ['total_rooms']}"
        assert occ["occupied_rooms"] == 0
        assert occ["vacant_rooms"] == 0
        assert occ["occupancy_rate"] == 0.0, f"Expected 0.0 occupancy rate, got {occ['occupancy_rate']}"
        assert occ["occupied_room_details"] == [], "Occupied room details must be empty list."
        print("[PASS] /analytics/occupancy-summary returned honest zero state (0 rooms, 0.0% rate).")
        
        # 2. Test /analytics/alert-summary
        status, alerts = api_call("/analytics/alert-summary", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {alerts}"
        assert alerts["total_alerts"] == 0
        assert alerts["status_counts"]["new"] == 0
        assert alerts["status_counts"]["acknowledged"] == 0
        assert alerts["status_counts"]["resolved"] == 0
        assert alerts["severity_counts"]["CRITICAL"] == 0
        print("[PASS] /analytics/alert-summary returned honest zero state (0 alerts).")

    finally:
        # Teardown test organization and user
        with Session(engine) as session:
            urs = session.exec(select(UserRole).where(UserRole.user_id == test_user_id)).all()
            for r in urs:
                session.delete(r)
            u = session.get(User, test_user_id)
            if u:
                session.delete(u)
            o = session.get(Organization, empty_org_id)
            if o:
                session.delete(o)
            session.commit()
        print("[PASS] Cleaned up temporary empty organization and test user.")

# ============================================================================
# 4. PROFILE PHOTO UPLOAD ANTI-DISGUISE & MAGIC-BYTE SECURITY
# ============================================================================
def test_photo_upload_magic_byte_anti_disguise():
    """
    Verifies that the photo upload pipeline:
    1. Rejects a non-image file disguised with an image filename (.png) via magic-byte sniffing.
    2. Rejects corrupt payload with valid magic bytes via Pillow verification.
    3. Accepts a genuine image and updates the profile photo.
    """
    print("\n--- 4. Testing Photo Upload Anti-Disguise & Magic-Byte Verification ---")
    
    auth = login(CAREGIVER_EMAIL, CAREGIVER_PASSWORD)
    token = auth["access_token"]
    
    # 1. Upload disguised text file with .png extension
    disguised_bytes = b"MZ executable or plain text content masquerading as a PNG image"
    status, res = upload_multipart(
        endpoint="/users/me/photo",
        field_name="file",
        filename="malicious_disguised.png",
        file_bytes=disguised_bytes,
        content_type="image/png",
        token=token
    )
    assert status == 400, f"Expected 400 Bad Request for disguised file, got {status}: {res}"
    assert "File must be a JPEG, PNG, GIF or WebP image" in str(res)
    print("[PASS] Disguised non-image payload rejected by magic-byte sniffer (HTTP 400).")
    
    # 2. Upload corrupt header with valid PNG signature prefix but invalid content
    corrupt_png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    status, res = upload_multipart(
        endpoint="/users/me/photo",
        field_name="file",
        filename="corrupt_signature.png",
        file_bytes=corrupt_png_bytes,
        content_type="image/png",
        token=token
    )
    assert status == 400, f"Expected 400 Bad Request for corrupt image, got {status}: {res}"
    assert "File is not a valid image" in str(res)
    print("[PASS] Corrupt payload rejected by Pillow image verifier (HTTP 400).")
    
    # 3. Upload genuine valid PNG image
    status, res = upload_multipart(
        endpoint="/users/me/photo",
        field_name="file",
        filename="valid_avatar.png",
        file_bytes=generate_valid_png(),
        content_type="image/png",
        token=token
    )
    assert status == 200, f"Expected 200 OK for valid PNG, got {status}: {res}"
    
    # Verify DB persistence of photo_url
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == CAREGIVER_EMAIL)).first()
        assert user is not None and user.photo_url is not None
        assert user.photo_url.startswith("/uploads/user_") and user.photo_url.endswith(".png")
        photo_url = user.photo_url
        print(f"[PASS] Genuine PNG accepted and processed successfully (DB photo_url: {photo_url}).")
        
        # Clean up uploaded file from disk and restore user photo_url
        try:
            uploaded_filename = photo_url.split("/")[-1]
            upload_dir = Path(__file__).resolve().parent / "app" / "uploads"
            uploaded_file_path = upload_dir / uploaded_filename
            if uploaded_file_path.exists():
                uploaded_file_path.unlink()
                print("[PASS] Removed uploaded test image file from disk.")
                
            user.photo_url = None
            session.add(user)
            session.commit()
            print("[PASS] Restored user photo_url state.")
        except Exception as e:
            print(f"Warning during photo cleanup: {e}")

if __name__ == "__main__":
    print("==========================================================================")
    print("      WIFISENSE BUSINESS LOGIC & TELEMETRY TEST SUITE (ITEM 3)            ")
    print("==========================================================================")
    test_sensing_event_creation_and_classification()
    test_alert_lifecycle_and_actor_attribution()
    test_analytics_empty_organization_unfabricated_data()
    test_photo_upload_magic_byte_anti_disguise()
    print("\n==========================================================================")
    print("           ALL ITEM 3 BUSINESS LOGIC TESTS PASSED 100%!                   ")
    print("==========================================================================")
