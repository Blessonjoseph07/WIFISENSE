"""
WIFISENSE GLOBAL / SYSTEM ADMINISTRATOR RBAC & ALERT OVERSIGHT TEST SUITE
========================================================================
Verifies the refined role responsibility model:
- System / Global Admin: Platform-wide READ & OVERSIGHT ONLY.
  Can view alerts, active alerts, enriched incident details, and timeline globally.
  Cannot acknowledge, mark responding, or resolve CARE alerts (HTTP 403 Forbidden).
- Facility Manager: Operational responder within facility scope.
  Can acknowledge, mark responding, and resolve CARE alerts.
- Caregiver: Primary operational responder within assigned scope.
  Can acknowledge, mark responding, and resolve CARE alerts.
- Family Member: Read-only sharing-policy gated access.
  Cannot acknowledge, mark responding, or resolve alerts (HTTP 403 Forbidden).

Tests:
- Test A: Global Admin can view CARE alerts, active alerts, and alert details
- Test B: Global Admin cannot acknowledge CARE alerts (HTTP 403 Forbidden)
- Test C: Global Admin cannot mark CARE alerts as responding (HTTP 403 Forbidden)
- Test D: Global Admin cannot resolve CARE alerts (HTTP 403 Forbidden)
- Test E: Elder Care Facility Manager can operate alerts (ack, responding, resolve)
- Test F: Caregiver can operate alerts (ack, responding, resolve)
- Test G: Family Member cannot operate alerts (ack, responding, resolve blocked with HTTP 403)
"""

import os
import json
import urllib.request
import urllib.error
import uuid
from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import hash_password
from app.models.entities import (
    User, Role, UserRole, Organization, Building, Floor, Room,
    SensingDevice, SensingEvent, ActivityType, Alert, AlertAcknowledgement,
    AuditLog, EmergencyContact, Resident
)

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# Test credentials
SYSADMIN_EMAIL = os.getenv("TEST_SYSADMIN_EMAIL", "blesson@wifisense.com")
SYSADMIN_PASSWORD = os.getenv("TEST_SYSADMIN_PASSWORD", "blessonpassword")

FACILITY_MANAGER_EMAIL = os.getenv("TEST_FM_EMAIL", "elizabeth@wifisense.com")
FACILITY_MANAGER_PASSWORD = os.getenv("TEST_FM_PASSWORD", "elizabethpassword")

CAREGIVER_EMAIL = os.getenv("TEST_CAREGIVER_EMAIL", "abhinanth@wifisense.com")
CAREGIVER_PASSWORD = os.getenv("TEST_CAREGIVER_PASSWORD", "abhinanthpassword")

FAMILY_EMAIL = os.getenv("TEST_FAMILY_EMAIL", "john@wifisense.com")
FAMILY_PASSWORD = os.getenv("TEST_FAMILY_PASSWORD", "johnpassword")

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

def create_test_fall_alert():
    """Creates a temporary CARE fall alert for testing."""
    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        assert device is not None, "Seeded sensing device not found."
        room = session.get(Room, device.room_id)
        assert room is not None
        
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            room_id=room.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Fall Detected in Resident Room",
            status="new",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(alert)
        session.commit()
        return alert_id

def cleanup_alert(alert_id):
    """Clean up a test alert and its acknowledgements."""
    with Session(engine) as session:
        acks = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).all()
        for a in acks:
            session.delete(a)
        alt = session.get(Alert, alert_id)
        if alt:
            session.delete(alt)
        session.commit()

# ============================================================================
# TEST A: GLOBAL ADMIN CAN VIEW CARE ALERTS, ACTIVE ALERTS, AND DETAILS
# ============================================================================
def test_a_global_admin_can_view():
    print("\n--- Test A: Global Admin Can View CARE Alerts (Global Oversight) ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]
    alert_id = create_test_fall_alert()

    try:
        # 1. View all alerts via GET /alerts
        status, alerts_list = api_call("/alerts", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {alerts_list}"
        found = any(a["id"] == alert_id for a in alerts_list)
        assert found, f"Created alert {alert_id} not found in GET /alerts."
        print(f"[PASS] Global Admin retrieved alert {alert_id} from GET /alerts.")

        # 2. View active alerts via GET /alerts/active
        status, active_list = api_call("/alerts/active", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {active_list}"
        found_active = any(a["id"] == alert_id for a in active_list)
        assert found_active, f"Created alert {alert_id} not found in GET /alerts/active."
        print(f"[PASS] Global Admin retrieved alert {alert_id} from GET /alerts/active.")

        # 3. View enriched alert details via GET /alerts/{id}
        status, detail = api_call(f"/alerts/{alert_id}", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {detail}"
        assert detail["id"] == alert_id
        assert detail["organization_name"] is not None
        assert detail["room_name"] is not None
        assert detail["resident_name"] is not None
        print(f"[PASS] Global Admin retrieved enriched alert details: Room {detail['room_name']}, Resident {detail['resident_name']}, Org {detail['organization_name']}.")
    finally:
        cleanup_alert(alert_id)

# ============================================================================
# TEST B: GLOBAL ADMIN CANNOT ACKNOWLEDGE CARE ALERTS
# ============================================================================
def test_b_global_admin_cannot_acknowledge():
    print("\n--- Test B: Global Admin Cannot Acknowledge CARE Alert ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]
    alert_id = create_test_fall_alert()

    try:
        status, res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=token)
        assert status == 403, f"Expected 403 Forbidden when Global Admin acknowledges alert, got {status}: {res}"
        print(f"[PASS] Global Admin cannot acknowledge CARE alert (HTTP {status}: {res.get('detail')}).")
    finally:
        cleanup_alert(alert_id)

# ============================================================================
# TEST C: GLOBAL ADMIN CANNOT MARK RESPONDING
# ============================================================================
def test_c_global_admin_cannot_mark_responding():
    print("\n--- Test C: Global Admin Cannot Mark CARE Alert As Responding ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]
    alert_id = create_test_fall_alert()

    try:
        status, res = api_call(f"/alerts/{alert_id}/responding", method="PATCH", token=token)
        assert status == 403, f"Expected 403 Forbidden when Global Admin marks alert as responding, got {status}: {res}"
        print(f"[PASS] Global Admin cannot mark CARE alert as responding (HTTP {status}: {res.get('detail')}).")
    finally:
        cleanup_alert(alert_id)

# ============================================================================
# TEST D: GLOBAL ADMIN CANNOT RESOLVE
# ============================================================================
def test_d_global_admin_cannot_resolve():
    print("\n--- Test D: Global Admin Cannot Resolve CARE Alert ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]
    alert_id = create_test_fall_alert()

    try:
        notes = "Attempted resolution by Global Admin"
        status, res = api_call(
            f"/alerts/{alert_id}/resolve",
            method="PATCH",
            token=token,
            data={"resolution_notes": notes}
        )
        assert status == 403, f"Expected 403 Forbidden when Global Admin resolves alert, got {status}: {res}"
        print(f"[PASS] Global Admin cannot resolve CARE alert (HTTP {status}: {res.get('detail')}).")
    finally:
        cleanup_alert(alert_id)

# ============================================================================
# TEST E: FACILITY MANAGER CAN OPERATE ALERTS
# ============================================================================
def test_e_facility_manager_can_operate_alerts():
    print("\n--- Test E: Facility Manager Can Operate Alerts (Ack -> Responding -> Resolve) ---")
    fm_auth = login(FACILITY_MANAGER_EMAIL, FACILITY_MANAGER_PASSWORD)
    fm_token = fm_auth["access_token"]
    fm_user_id = fm_auth["user"]["id"]
    alert_id = create_test_fall_alert()

    try:
        # 1. Acknowledge
        status, ack_res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=fm_token)
        assert status == 200, f"Expected 200 OK for Facility Manager on /acknowledge, got {status}: {ack_res}"
        assert ack_res["status"] == "acknowledged"
        print(f"[PASS] Facility Manager acknowledged alert {alert_id} (HTTP 200).")

        # 2. Mark Responding
        status, resp_res = api_call(f"/alerts/{alert_id}/responding", method="PATCH", token=fm_token)
        assert status == 200, f"Expected 200 OK for Facility Manager on /responding, got {status}: {resp_res}"
        assert resp_res["status"] == "responding"
        print(f"[PASS] Facility Manager marked alert as responding (HTTP 200).")

        # 3. Resolve
        res_notes = "Facility Manager coordinated on-site nurse response. Resident safe."
        status, resolve_res = api_call(
            f"/alerts/{alert_id}/resolve",
            method="PATCH",
            token=fm_token,
            data={"resolution_notes": res_notes}
        )
        assert status == 200, f"Expected 200 OK for Facility Manager on /resolve, got {status}: {resolve_res}"
        assert resolve_res["status"] == "resolved"
        print(f"[PASS] Facility Manager resolved alert (HTTP 200).")

        # Verify attribution in AlertAcknowledgement & AuditLog
        with Session(engine) as session:
            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is not None
            assert ack.user_id == fm_user_id
            assert ack.resolution_notes == res_notes
            print(f"[PASS] AlertAcknowledgement attributed to Facility Manager {fm_user_id}.")

            audit = session.exec(
                select(AuditLog).where(
                    AuditLog.resource_id == alert_id,
                    AuditLog.what_action == "ALERT_RESOLVED"
                )
            ).first()
            assert audit is not None
            assert audit.who_user_id == fm_user_id
            print(f"[PASS] AuditLog recorded for ALERT_RESOLVED by Facility Manager {audit.who_email}.")
    finally:
        cleanup_alert(alert_id)

# ============================================================================
# TEST F: CAREGIVER CAN OPERATE ALERTS
# ============================================================================
def test_f_caregiver_can_operate_alerts():
    print("\n--- Test F: Caregiver Can Operate Alerts (Ack -> Responding -> Resolve) ---")
    cg_auth = login(CAREGIVER_EMAIL, CAREGIVER_PASSWORD)
    cg_token = cg_auth["access_token"]
    cg_user_id = cg_auth["user"]["id"]
    alert_id = create_test_fall_alert()

    try:
        # 1. Acknowledge
        status, ack_res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=cg_token)
        assert status == 200, f"Expected 200 OK for Caregiver on /acknowledge, got {status}: {ack_res}"
        assert ack_res["status"] == "acknowledged"
        print(f"[PASS] Caregiver acknowledged alert {alert_id} (HTTP 200).")

        # 2. Mark Responding
        status, resp_res = api_call(f"/alerts/{alert_id}/responding", method="PATCH", token=cg_token)
        assert status == 200, f"Expected 200 OK for Caregiver on /responding, got {status}: {resp_res}"
        assert resp_res["status"] == "responding"
        print(f"[PASS] Caregiver marked alert as responding (HTTP 200).")

        # 3. Resolve
        res_notes = "Caregiver assisted resident back to bed. Vitals normal."
        status, resolve_res = api_call(
            f"/alerts/{alert_id}/resolve",
            method="PATCH",
            token=cg_token,
            data={"resolution_notes": res_notes}
        )
        assert status == 200, f"Expected 200 OK for Caregiver on /resolve, got {status}: {resolve_res}"
        assert resolve_res["status"] == "resolved"
        print(f"[PASS] Caregiver resolved alert (HTTP 200).")

        # Verify attribution
        with Session(engine) as session:
            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is not None
            assert ack.user_id == cg_user_id
            assert ack.resolution_notes == res_notes
            print(f"[PASS] AlertAcknowledgement attributed to Caregiver {cg_user_id}.")

            audit = session.exec(
                select(AuditLog).where(
                    AuditLog.resource_id == alert_id,
                    AuditLog.what_action == "ALERT_RESOLVED"
                )
            ).first()
            assert audit is not None
            assert audit.who_user_id == cg_user_id
            print(f"[PASS] AuditLog recorded for ALERT_RESOLVED by Caregiver {audit.who_email}.")
    finally:
        cleanup_alert(alert_id)

# ============================================================================
# TEST G: FAMILY MEMBER CANNOT OPERATE ALERTS
# ============================================================================
def test_g_family_member_cannot_operate_alerts():
    print("\n--- Test G: Family Member Cannot Operate Alerts ---")
    fam_auth = login(FAMILY_EMAIL, FAMILY_PASSWORD)
    fam_token = fam_auth["access_token"]
    alert_id = create_test_fall_alert()

    try:
        # 1. Family Member attempts GET /alerts -> 403 Forbidden
        status, res = api_call("/alerts", method="GET", token=fam_token)
        assert status == 403, f"Expected 403 Forbidden on GET /alerts for Family Member, got {status}: {res}"
        print(f"[PASS] Family Member blocked from GET /alerts (HTTP {status}).")

        # 2. Family Member attempts PATCH /alerts/{id}/acknowledge -> 403 Forbidden
        status, res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=fam_token)
        assert status == 403, f"Expected 403 Forbidden on PATCH /acknowledge for Family Member, got {status}: {res}"
        print(f"[PASS] Family Member blocked from PATCH /acknowledge (HTTP {status}).")

        # 3. Family Member attempts PATCH /alerts/{id}/responding -> 403 Forbidden
        status, res = api_call(f"/alerts/{alert_id}/responding", method="PATCH", token=fam_token)
        assert status == 403, f"Expected 403 Forbidden on PATCH /responding for Family Member, got {status}: {res}"
        print(f"[PASS] Family Member blocked from PATCH /responding (HTTP {status}).")

        # 4. Family Member attempts PATCH /alerts/{id}/resolve -> 403 Forbidden
        status, res = api_call(
            f"/alerts/{alert_id}/resolve",
            method="PATCH",
            token=fam_token,
            data={"resolution_notes": "Family notes"}
        )
        assert status == 403, f"Expected 403 Forbidden on PATCH /resolve for Family Member, got {status}: {res}"
        print(f"[PASS] Family Member blocked from PATCH /resolve (HTTP {status}).")
    finally:
        cleanup_alert(alert_id)

if __name__ == "__main__":
    print("==========================================================================")
    print("   WIFISENSE REFINED RBAC & ALERT OVERSIGHT VERIFICATION SUITE           ")
    print("==========================================================================")
    test_a_global_admin_can_view()
    test_b_global_admin_cannot_acknowledge()
    test_c_global_admin_cannot_mark_responding()
    test_d_global_admin_cannot_resolve()
    test_e_facility_manager_can_operate_alerts()
    test_f_caregiver_can_operate_alerts()
    test_g_family_member_cannot_operate_alerts()
    print("\n==========================================================================")
    print("      ALL REFINED RBAC & ALERT OVERSIGHT TESTS PASSED 100%!               ")
    print("==========================================================================")
