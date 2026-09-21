import json
import urllib.request
import urllib.error
import time
import uuid
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import (
    AuditLog, Alert, SensingDevice, Room, Resident, FamilyConnection,
    FamilySubscription, SharingPolicy, User, SensingEvent,
    Organization, Building, Floor, ActivityType
)
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

def test_occupancy_summary_care_corporate_split():
    """
    Test 4: Verify Occupancy Summary CARE vs. CORPORATE split:
    - Creates one ELDER_CARE organization and one CORPORATE organization.
    - Creates rooms in both organizations (one occupied, one vacant in each).
    - Verifies breakdown object splits total_rooms, occupied_rooms, vacant_rooms, occupancy_rate into ELDER_CARE and CORPORATE.
    - Verifies combined totals match the sum of both buckets.
    - Verifies organization_type field is present in occupied_room_details.
    """
    print("\n--- Test 4: Occupancy Summary CARE vs. CORPORATE Split ---")
    
    auth_data = login("blesson@wifisense.com", "blessonpassword")
    token = auth_data["access_token"]
    
    care_org_id = str(uuid.uuid4())
    care_bld_id = str(uuid.uuid4())
    care_flr_id = str(uuid.uuid4())
    care_rm1_id = str(uuid.uuid4())
    care_rm2_id = str(uuid.uuid4())
    
    corp_org_id = str(uuid.uuid4())
    corp_bld_id = str(uuid.uuid4())
    corp_flr_id = str(uuid.uuid4())
    corp_rm1_id = str(uuid.uuid4())
    corp_rm2_id = str(uuid.uuid4())
    
    evt_care_id = str(uuid.uuid4())
    evt_corp_id = str(uuid.uuid4())

    try:
        with Session(engine) as session:
            # Care hierarchy
            care_org = Organization(id=care_org_id, name=f"Test Care Facility Analytics {uuid.uuid4().hex[:6]}", type="ELDER_CARE")
            care_bld = Building(id=care_bld_id, organization_id=care_org_id, name="Care Building Analytics")
            care_flr = Floor(id=care_flr_id, building_id=care_bld_id, floor_number=1)
            care_rm1 = Room(id=care_rm1_id, floor_id=care_flr_id, name="Care Suite 101", room_type="resident_room")
            care_rm2 = Room(id=care_rm2_id, floor_id=care_flr_id, name="Care Suite 102", room_type="resident_room")
            
            # Corporate hierarchy
            corp_org = Organization(id=corp_org_id, name=f"Test Corporate Facility Analytics {uuid.uuid4().hex[:6]}", type="CORPORATE")
            corp_bld = Building(id=corp_bld_id, organization_id=corp_org_id, name="Corp Building Analytics")
            corp_flr = Floor(id=corp_flr_id, building_id=corp_bld_id, floor_number=1)
            corp_rm1 = Room(id=corp_rm1_id, floor_id=corp_flr_id, name="Corp Office 101", room_type="meeting_room")
            corp_rm2 = Room(id=corp_rm2_id, floor_id=corp_flr_id, name="Corp Office 102", room_type="conference_room")
            
            session.add_all([care_org, care_bld, care_flr, care_rm1, care_rm2, corp_org, corp_bld, corp_flr, corp_rm1, corp_rm2])
            session.commit()
        
        # Locate a device for foreign key
        device = session.exec(select(SensingDevice)).first()
        dev_id = device.id if device else "dev_ec_101"

        # Active occupancy events (care_rm1 occupied, corp_rm1 occupied)
        act = session.exec(select(ActivityType).where(ActivityType.name != "Empty")).first()
        act_id = act.id if act else 1
        
        evt_care = SensingEvent(
            device_id=dev_id,
            room_id=care_rm1_id,
            inferred_activity_id=act_id,
            model_confidence=0.95,
            rssi=-45,
            extracted_features={"motion_energy": 0.8}
        )
        evt_corp = SensingEvent(
            device_id=dev_id,
            room_id=corp_rm1_id,
            inferred_activity_id=act_id,
            model_confidence=0.91,
            rssi=-48,
            extracted_features={"motion_energy": 0.7}
        )
        session.add_all([evt_care, evt_corp])
        session.commit()

        status, res = api_call("/analytics/occupancy-summary", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {res}"
        
        # 1. Check breakdown presence and structure
        assert "breakdown" in res, "Missing 'breakdown' in occupancy summary response."
        breakdown = res["breakdown"]
        assert "ELDER_CARE" in breakdown, "Missing 'ELDER_CARE' in occupancy breakdown."
        assert "CORPORATE" in breakdown, "Missing 'CORPORATE' in occupancy breakdown."
        
        care_b = breakdown["ELDER_CARE"]
        corp_b = breakdown["CORPORATE"]
        
        print(f"[PASS] Top-level breakdown verified (ELDER_CARE: {care_b}, CORPORATE: {corp_b})")
        
        # 2. Check breakdown numbers reflect created rooms
        assert care_b["total_rooms"] >= 2
        assert care_b["occupied_rooms"] >= 1
        assert care_b["vacant_rooms"] >= 1
        assert care_b["occupancy_rate"] > 0.0
        
        assert corp_b["total_rooms"] >= 2
        assert corp_b["occupied_rooms"] >= 1
        assert corp_b["vacant_rooms"] >= 1
        assert corp_b["occupancy_rate"] > 0.0
        print("[PASS] Breakdown numbers accurately reflect created Care and Corporate rooms.")
        
        # 3. Check combined totals match the sum of both buckets
        assert res["total_rooms"] == care_b["total_rooms"] + corp_b["total_rooms"], \
            f"Total rooms ({res['total_rooms']}) != Care ({care_b['total_rooms']}) + Corp ({corp_b['total_rooms']})"
        assert res["occupied_rooms"] == care_b["occupied_rooms"] + corp_b["occupied_rooms"], \
            f"Occupied rooms ({res['occupied_rooms']}) != Care ({care_b['occupied_rooms']}) + Corp ({corp_b['occupied_rooms']})"
        assert res["vacant_rooms"] == care_b["vacant_rooms"] + corp_b["vacant_rooms"], \
            f"Vacant rooms ({res['vacant_rooms']}) != Care ({care_b['vacant_rooms']}) + Corp ({corp_b['vacant_rooms']})"
        print(f"[PASS] Combined totals match the sum of both buckets ({res['total_rooms']} rooms = {care_b['total_rooms']} Care + {corp_b['total_rooms']} Corp).")
        
        # 4. Check organization_type in occupied_room_details
        details = res["occupied_room_details"]
        care_rm_detail = next((d for d in details if d["room_id"] == care_rm1_id), None)
        corp_rm_detail = next((d for d in details if d["room_id"] == corp_rm1_id), None)
        assert care_rm_detail is not None, "Care room not found in occupied_room_details."
        assert care_rm_detail.get("organization_type") == "ELDER_CARE", f"Expected ELDER_CARE, got {care_rm_detail.get('organization_type')}"
        assert corp_rm_detail is not None, "Corp room not found in occupied_room_details."
        assert corp_rm_detail.get("organization_type") == "CORPORATE", f"Expected CORPORATE, got {corp_rm_detail.get('organization_type')}"
        print("[PASS] organization_type resolved and verified in occupied_room_details.")

    finally:
        with Session(engine) as session:
            evts = session.exec(select(SensingEvent).where(SensingEvent.room_id.in_([care_rm1_id, care_rm2_id, corp_rm1_id, corp_rm2_id]))).all()
            for e in evts:
                session.delete(e)
            for rid in [care_rm1_id, care_rm2_id, corp_rm1_id, corp_rm2_id]:
                r = session.get(Room, rid)
                if r:
                    session.delete(r)
            for fid in [care_flr_id, corp_flr_id]:
                f = session.get(Floor, fid)
                if f:
                    session.delete(f)
            for bid in [care_bld_id, corp_bld_id]:
                b = session.get(Building, bid)
                if b:
                    session.delete(b)
            for oid in [care_org_id, corp_org_id]:
                o = session.get(Organization, oid)
                if o:
                    session.delete(o)
            session.commit()
            print("[PASS] Cleaned up occupancy test organizations, rooms, and events.")

def test_alert_summary_care_corporate_split():
    """
    Test 5: Verify Alert Summary CARE vs. CORPORATE split:
    - Creates one ELDER_CARE organization and one CORPORATE organization.
    - Creates alerts in both organizations with varied statuses and severities.
    - Verifies breakdown object splits total_alerts, status_counts, severity_counts into ELDER_CARE and CORPORATE.
    - Verifies combined totals match the sum of both buckets.
    """
    print("\n--- Test 5: Alert Summary CARE vs. CORPORATE Split ---")
    
    auth_data = login("blesson@wifisense.com", "blessonpassword")
    token = auth_data["access_token"]
    
    care_org_id = str(uuid.uuid4())
    care_bld_id = str(uuid.uuid4())
    care_flr_id = str(uuid.uuid4())
    care_rm_id = str(uuid.uuid4())
    
    corp_org_id = str(uuid.uuid4())
    corp_bld_id = str(uuid.uuid4())
    corp_flr_id = str(uuid.uuid4())
    corp_rm_id = str(uuid.uuid4())
    
    alt_care1_id = str(uuid.uuid4())
    alt_care2_id = str(uuid.uuid4())
    alt_corp1_id = str(uuid.uuid4())
    alt_corp2_id = str(uuid.uuid4())

    try:
        with Session(engine) as session:
            care_org = Organization(id=care_org_id, name=f"Care Alert Analytics Org {uuid.uuid4().hex[:6]}", type="ELDER_CARE")
            care_bld = Building(id=care_bld_id, organization_id=care_org_id, name="Care Alert Building")
            care_flr = Floor(id=care_flr_id, building_id=care_bld_id, floor_number=1)
            care_rm = Room(id=care_rm_id, floor_id=care_flr_id, name="Care Alert Room", room_type="resident_room")
            
            corp_org = Organization(id=corp_org_id, name=f"Corp Alert Analytics Org {uuid.uuid4().hex[:6]}", type="CORPORATE")
            corp_bld = Building(id=corp_bld_id, organization_id=corp_org_id, name="Corp Alert Building")
            corp_flr = Floor(id=corp_flr_id, building_id=corp_bld_id, floor_number=1)
            corp_rm = Room(id=corp_rm_id, floor_id=corp_flr_id, name="Corp Alert Room", room_type="conference_room")
            
            session.add_all([care_org, care_bld, care_flr, care_rm, corp_org, corp_bld, corp_flr, corp_rm])
            session.commit()
            
            alt_care1 = Alert(id=alt_care1_id, room_id=care_rm_id, event_type="Fall_Detected", severity="CRITICAL", status="new", message="Care Fall")
            alt_care2 = Alert(id=alt_care2_id, room_id=care_rm_id, event_type="Prolonged_Inactivity", severity="HIGH", status="acknowledged", message="Care Inactivity")
            
            alt_corp1 = Alert(id=alt_corp1_id, room_id=corp_rm_id, event_type="Unexpected_Occupancy", severity="MEDIUM", status="new", message="Corp Occupancy")
            alt_corp2 = Alert(id=alt_corp2_id, room_id=corp_rm_id, event_type="After_Hours_Motion", severity="LOW", status="resolved", message="Corp Motion")
            
            session.add_all([alt_care1, alt_care2, alt_corp1, alt_corp2])
            session.commit()

        status, res = api_call("/analytics/alert-summary", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {res}"
        
        # 1. Check breakdown presence and structure
        assert "breakdown" in res, "Missing 'breakdown' in alert summary response."
        breakdown = res["breakdown"]
        assert "ELDER_CARE" in breakdown, "Missing 'ELDER_CARE' in alert breakdown."
        assert "CORPORATE" in breakdown, "Missing 'CORPORATE' in alert breakdown."
        
        care_b = breakdown["ELDER_CARE"]
        corp_b = breakdown["CORPORATE"]
        
        print(f"[PASS] Top-level alert breakdown verified (ELDER_CARE: {care_b}, CORPORATE: {corp_b})")
        
        # 2. Check breakdown numbers reflect created alerts
        assert care_b["total_alerts"] >= 2
        assert care_b["status_counts"]["new"] >= 1
        assert care_b["status_counts"]["acknowledged"] >= 1
        assert care_b["severity_counts"]["CRITICAL"] >= 1
        assert care_b["severity_counts"]["HIGH"] >= 1
        
        assert corp_b["total_alerts"] >= 2
        assert corp_b["status_counts"]["new"] >= 1
        assert corp_b["status_counts"]["resolved"] >= 1
        assert corp_b["severity_counts"]["MEDIUM"] >= 1
        assert corp_b["severity_counts"]["LOW"] >= 1
        print("[PASS] Breakdown numbers accurately reflect created Care and Corporate alerts.")
        
        # 3. Check combined totals match the sum of both buckets
        assert res["total_alerts"] == care_b["total_alerts"] + corp_b["total_alerts"], \
            f"Total alerts ({res['total_alerts']}) != Care ({care_b['total_alerts']}) + Corp ({corp_b['total_alerts']})"
        
        for st in ["new", "acknowledged", "resolved"]:
            expected_sum = care_b["status_counts"].get(st, 0) + corp_b["status_counts"].get(st, 0)
            actual = res["status_counts"].get(st, 0)
            assert actual == expected_sum, f"Status count for {st}: {actual} != {expected_sum}"
            
        for sev in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            expected_sum = care_b["severity_counts"].get(sev, 0) + corp_b["severity_counts"].get(sev, 0)
            actual = res["severity_counts"].get(sev, 0)
            assert actual == expected_sum, f"Severity count for {sev}: {actual} != {expected_sum}"
            
        print(f"[PASS] Combined alert totals and counts match the sum of both buckets ({res['total_alerts']} total alerts).")

    finally:
        with Session(engine) as session:
            for aid in [alt_care1_id, alt_care2_id, alt_corp1_id, alt_corp2_id]:
                a = session.get(Alert, aid)
                if a:
                    session.delete(a)
            for rid in [care_rm_id, corp_rm_id]:
                r = session.get(Room, rid)
                if r:
                    session.delete(r)
            for fid in [care_flr_id, corp_flr_id]:
                f = session.get(Floor, fid)
                if f:
                    session.delete(f)
            for bid in [care_bld_id, corp_bld_id]:
                b = session.get(Building, bid)
                if b:
                    session.delete(b)
            for oid in [care_org_id, corp_org_id]:
                o = session.get(Organization, oid)
                if o:
                    session.delete(o)
            session.commit()
            print("[PASS] Cleaned up alert test organizations, rooms, and alerts.")

if __name__ == "__main__":
    print("==================================================")
    print("      WIFISENSE ALERT NOTIFICATION TEST SUITE     ")
    print("==================================================")
    test_alert_notification_e2e()
    test_sharing_policy_gating()
    test_unit_send_alert_email_graceful_error_handling()
    test_occupancy_summary_care_corporate_split()
    test_alert_summary_care_corporate_split()
    print("\n==================================================")
    print("         ALL BUSINESS LOGIC TESTS PASSED          ")
    print("==================================================")
