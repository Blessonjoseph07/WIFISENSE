"""
WIFISENSE GLOBAL / SYSTEM ADMINISTRATOR ALERT ACCESS TEST SUITE
==============================================================
Verifies that System / Global Administrator can perform platform-wide
administration and respond operationally to elder-care incidents (view,
acknowledge, resolve), while preserving strict organization isolation for
scoped roles, preventing Family Member privilege escalation, and ensuring
all actions are recorded in the AuditLog.

Tests implemented:
- Test A: Global Admin can view CARE fall alerts (GET /alerts, GET /alerts/active, GET /alerts/{id})
- Test B: Global Admin can acknowledge fall alert (PATCH /alerts/{id}/acknowledge)
- Test C: Global Admin can resolve fall alert (PATCH /alerts/{id}/resolve)
- Test D: Invalid lifecycle remains blocked (e.g. resolved -> acknowledged returns HTTP 400)
- Test E: Multi-tenant organization isolation remains intact (Org Admin A cannot access Org B)
- Test F: Family Member cannot acknowledge or resolve fall alerts (HTTP 403)
- Test G: Legacy emergency_contact role is rejected from alert actions & Family Portal (HTTP 403)
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

# ============================================================================
# TEST A: GLOBAL ADMIN CAN VIEW CARE FALL ALERTS
# ============================================================================
def test_a_global_admin_can_view_care_fall_alert():
    print("\n--- Test A: Global Admin Can View CARE Fall Alert ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]

    # 1. Trigger or find a CARE fall alert
    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        assert device is not None, "Seeded sensing device not found."
        device_id = device.id

    status, sim_res = api_call(
        "/sensing/simulate-event",
        method="POST",
        token=token,
        data={
            "device_id": device_id,
            "simulated_activity": "Fall_Detected"
        }
    )
    assert status == 201
    assert sim_res["alert_triggered"] is True
    alert_id = sim_res["alert"]["id"]
    event_id = sim_res["sensing_event"]["id"]

    try:
        # Verify Global Admin sees alert in list GET /alerts
        status, alerts_list = api_call("/alerts", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {alerts_list}"
        found_in_list = any(a["id"] == alert_id for a in alerts_list)
        assert found_in_list, "Created fall alert must be visible to Global Admin in GET /alerts."
        print(f"[PASS] Global Admin retrieved alert {alert_id} from GET /alerts.")

        # Verify Global Admin sees alert in GET /alerts/active
        status, active_list = api_call("/alerts/active", method="GET", token=token)
        assert status == 200
        found_in_active = any(a["id"] == alert_id for a in active_list)
        assert found_in_active, "Active fall alert must be visible to Global Admin in GET /alerts/active."
        print(f"[PASS] Global Admin retrieved alert {alert_id} from GET /alerts/active.")

        # Verify Global Admin retrieves enriched details via GET /alerts/{id}
        status, detail = api_call(f"/alerts/{alert_id}", method="GET", token=token)
        assert status == 200, f"Expected 200, got {status}: {detail}"
        assert detail["id"] == alert_id
        assert detail["event_type"] == "Fall_Detected"
        assert detail["severity"] == "CRITICAL"
        assert detail["status"] == "new"
        assert detail["room_name"] is not None
        assert detail["resident_name"] is not None
        assert detail["organization_name"] is not None
        assert detail["emergency_contact"] is not None
        print(f"[PASS] Global Admin retrieved enriched alert details: Room {detail['room_name']}, Resident {detail['resident_name']}, Org {detail['organization_name']}.")
    finally:
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

# ============================================================================
# TEST B: GLOBAL ADMIN CAN ACKNOWLEDGE FALL ALERT
# ============================================================================
def test_b_global_admin_can_acknowledge_fall_alert():
    print("\n--- Test B: Global Admin Can Acknowledge Fall Alert ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]
    sys_user_id = sys_auth["user"]["id"]

    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        device_id = device.id

    status, sim_res = api_call(
        "/sensing/simulate-event",
        method="POST",
        token=token,
        data={
            "device_id": device_id,
            "simulated_activity": "Fall_Detected"
        }
    )
    assert status == 201
    alert_id = sim_res["alert"]["id"]
    event_id = sim_res["sensing_event"]["id"]

    try:
        # Acknowledge as Global Admin
        status, ack_res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=token)
        assert status == 200, f"Expected 200, got {status}: {ack_res}"
        assert ack_res["status"] == "acknowledged"
        print(f"[PASS] Global Admin acknowledged alert {alert_id} (HTTP 200).")

        # Verify in database: AlertAcknowledgement and AuditLog
        with Session(engine) as session:
            db_alert = session.get(Alert, alert_id)
            assert db_alert.status == "acknowledged"

            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is not None, "AlertAcknowledgement record must exist."
            assert ack.user_id == sys_user_id, f"Expected acting user {sys_user_id}, got {ack.user_id}"
            assert ack.who_user_id == sys_user_id, f"Expected who_user_id {sys_user_id}, got {ack.who_user_id}"
            assert ack.acknowledged_at is not None, "acknowledged_at must be populated."
            print(f"[PASS] AlertAcknowledgement verified: acting user {ack.who_user_id} at {ack.acknowledged_at}.")

            audit = session.exec(
                select(AuditLog).where(
                    AuditLog.resource_id == alert_id,
                    AuditLog.what_action == "ALERT_ACKNOWLEDGED"
                )
            ).first()
            assert audit is not None, "AuditLog for ALERT_ACKNOWLEDGED must exist."
            assert audit.who_user_id == sys_user_id
            assert audit.details is not None and "organization_id" in audit.details
            print(f"[PASS] AuditLog verified: {audit.what_action} by Global Admin {audit.who_email} (Org: {audit.details.get('organization_id')}).")
    finally:
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

# ============================================================================
# TEST C: GLOBAL ADMIN CAN RESOLVE FALL ALERT
# ============================================================================
def test_c_global_admin_can_resolve_fall_alert():
    print("\n--- Test C: Global Admin Can Resolve Fall Alert ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]
    sys_user_id = sys_auth["user"]["id"]

    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        device_id = device.id

    status, sim_res = api_call(
        "/sensing/simulate-event",
        method="POST",
        token=token,
        data={
            "device_id": device_id,
            "simulated_activity": "Fall_Detected"
        }
    )
    assert status == 201
    alert_id = sim_res["alert"]["id"]
    event_id = sim_res["sensing_event"]["id"]

    try:
        # Acknowledge first
        api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=token)

        # Resolve with resolution notes
        notes = "Global Admin intervention: Coordinated on-site response with care desk. Resident assisted safely."
        status, res_res = api_call(
            f"/alerts/{alert_id}/resolve",
            method="PATCH",
            token=token,
            data={"resolution_notes": notes}
        )
        assert status == 200, f"Expected 200, got {status}: {res_res}"
        assert res_res["status"] == "resolved"
        print(f"[PASS] Global Admin resolved alert {alert_id} (HTTP 200).")

        with Session(engine) as session:
            db_alert = session.get(Alert, alert_id)
            assert db_alert.status == "resolved"

            ack = session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == alert_id)).first()
            assert ack is not None
            assert ack.resolved_at is not None, "resolved_at must be populated."
            assert ack.resolution_notes == notes, "resolution_notes must match submitted notes."
            print(f"[PASS] AlertAcknowledgement verified: resolved_at {ack.resolved_at} with notes: '{ack.resolution_notes}'.")

            audit = session.exec(
                select(AuditLog).where(
                    AuditLog.resource_id == alert_id,
                    AuditLog.what_action == "ALERT_RESOLVED"
                )
            ).first()
            assert audit is not None
            assert audit.who_user_id == sys_user_id
            assert audit.details.get("resolution_notes") == notes
            print(f"[PASS] AuditLog verified: {audit.what_action} by Global Admin {audit.who_email}.")
    finally:
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

# ============================================================================
# TEST D: INVALID LIFECYCLE REMAINS BLOCKED
# ============================================================================
def test_d_invalid_lifecycle_remains_blocked():
    print("\n--- Test D: Invalid Lifecycle State Transitions Remain Blocked ---")
    sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    token = sys_auth["access_token"]

    with Session(engine) as session:
        device = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "24:0A:C4:00:20:01")).first()
        device_id = device.id

    status, sim_res = api_call(
        "/sensing/simulate-event",
        method="POST",
        token=token,
        data={
            "device_id": device_id,
            "simulated_activity": "Fall_Detected"
        }
    )
    alert_id = sim_res["alert"]["id"]
    event_id = sim_res["sensing_event"]["id"]

    try:
        # Move directly to resolved
        api_call(f"/alerts/{alert_id}/resolve", method="PATCH", token=token, data={"resolution_notes": "Immediate resolution."})

        # Attempt to re-acknowledge already resolved alert
        status, err_res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=token)
        assert status == 400, f"Expected 400 Bad Request when acknowledging resolved alert, got {status}: {err_res}"
        print(f"[PASS] Attempt to acknowledge resolved alert correctly rejected with HTTP 400: {err_res}")

        # Attempt to mark already resolved alert as responding
        status, err_resp = api_call(f"/alerts/{alert_id}/responding", method="PATCH", token=token)
        assert status == 400, f"Expected 400 Bad Request when marking resolved alert as responding, got {status}: {err_resp}"
        print(f"[PASS] Attempt to mark resolved alert as responding correctly rejected with HTTP 400: {err_resp}")
    finally:
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

# ============================================================================
# TEST E: MULTI-TENANT ORGANIZATION ISOLATION REMAINS INTACT
# ============================================================================
def test_e_organization_isolation_remains_intact():
    print("\n--- Test E: Multi-Tenant Organization Isolation Remains Intact ---")
    # Provision two isolated organizations: Org A and Org B
    org_a_id = str(uuid.uuid4())
    org_b_id = str(uuid.uuid4())
    admin_a_id = str(uuid.uuid4())
    email_a = f"admin_a_{uuid.uuid4().hex[:6]}@test.com"
    password_a = "Pass12345!"

    bld_b_id = str(uuid.uuid4())
    flr_b_id = str(uuid.uuid4())
    rm_b_id = str(uuid.uuid4())
    alert_b_id = str(uuid.uuid4())

    with Session(engine) as session:
        # Create Org A and Org Admin A
        org_a = Organization(id=org_a_id, name="Facility Alpha", type="ELDER_CARE")
        session.add(org_a)
        user_a = User(id=admin_a_id, email=email_a, password_hash=hash_password(password_a), first_name="Admin", last_name="Alpha", is_active=True)
        session.add(user_a)
        ur_a = UserRole(user_id=admin_a_id, role_id=2, organization_id=org_a_id) # organization_admin
        session.add(ur_a)

        # Create Org B with an alert
        org_b = Organization(id=org_b_id, name="Facility Beta", type="ELDER_CARE")
        session.add(org_b)
        bld_b = Building(id=bld_b_id, organization_id=org_b_id, name="Beta Tower")
        session.add(bld_b)
        flr_b = Floor(id=flr_b_id, building_id=bld_b_id, floor_number=1)
        session.add(flr_b)
        rm_b = Room(id=rm_b_id, floor_id=flr_b_id, name="Beta Room 101", room_type="Bedroom")
        session.add(rm_b)
        alt_b = Alert(id=alert_b_id, room_id=rm_b_id, event_type="Fall_Detected", severity="CRITICAL", message="Fall in Beta Room", status="new")
        session.add(alt_b)
        session.commit()

    try:
        # Login as Admin A
        auth_a = login(email_a, password_a)
        token_a = auth_a["access_token"]

        # 1. Admin A queries GET /alerts -> must NOT include Alert B
        status, alerts_a = api_call("/alerts", method="GET", token=token_a)
        assert status == 200
        assert not any(a["id"] == alert_b_id for a in alerts_a), "Org Admin A must NOT see Alert B from Organization B."
        print("[PASS] Scoped query isolation: Alert B not visible to Org Admin A in GET /alerts.")

        # 2. Admin A attempts GET /alerts/{alert_b_id} -> must return 404
        status, res_detail = api_call(f"/alerts/{alert_b_id}", method="GET", token=token_a)
        assert status == 404, f"Expected 404 Not Found for out-of-scope alert, got {status}: {res_detail}"
        print("[PASS] Scoped direct read isolation: GET /alerts/{id} correctly rejected with HTTP 404.")

        # 3. Admin A attempts PATCH /alerts/{alert_b_id}/acknowledge -> must return 404
        status, res_ack = api_call(f"/alerts/{alert_b_id}/acknowledge", method="PATCH", token=token_a)
        assert status == 404, f"Expected 404 Not Found on cross-org acknowledge, got {status}: {res_ack}"
        print("[PASS] Scoped operational action isolation: PATCH /acknowledge rejected with HTTP 404.")

        # 4. Global Admin queries GET /alerts/{alert_b_id} -> MUST succeed (Platform-wide scope)
        sys_auth = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
        status, sys_detail = api_call(f"/alerts/{alert_b_id}", method="GET", token=sys_auth["access_token"])
        assert status == 200, f"Global Admin should access cross-org alert, got {status}: {sys_detail}"
        assert sys_detail["organization_name"] == "Facility Beta"
        print("[PASS] Global Admin platform-wide visibility confirmed: successfully accessed Alert B.")
    finally:
        with Session(engine) as session:
            a = session.get(Alert, alert_b_id)
            if a: session.delete(a)
            r = session.get(Room, rm_b_id)
            if r: session.delete(r)
            f = session.get(Floor, flr_b_id)
            if f: session.delete(f)
            b = session.get(Building, bld_b_id)
            if b: session.delete(b)
            ob = session.get(Organization, org_b_id)
            if ob: session.delete(ob)
            ura = session.exec(select(UserRole).where(UserRole.user_id == admin_a_id)).all()
            for ur in ura: session.delete(ur)
            ua = session.get(User, admin_a_id)
            if ua: session.delete(ua)
            oa = session.get(Organization, org_a_id)
            if oa: session.delete(oa)
            session.commit()

# ============================================================================
# TEST F: FAMILY MEMBER CANNOT ACKNOWLEDGE OR RESOLVE
# ============================================================================
def test_f_family_member_cannot_acknowledge_or_resolve():
    print("\n--- Test F: Family Member Cannot Acknowledge Or Resolve Alerts ---")
    fam_auth = login(FAMILY_EMAIL, FAMILY_PASSWORD)
    fam_token = fam_auth["access_token"]

    with Session(engine) as session:
        # Pick any seeded alert or create one
        alt = session.exec(select(Alert).where(Alert.status != "resolved")).first()
        assert alt is not None, "Active alert required for test."
        alert_id = alt.id

    # 1. Family Member attempts GET /alerts -> 403 Forbidden
    status, res = api_call("/alerts", method="GET", token=fam_token)
    assert status == 403, f"Expected 403 Forbidden for Family Member on GET /alerts, got {status}: {res}"
    print("[PASS] Family Member blocked from GET /alerts (HTTP 403).")

    # 2. Family Member attempts PATCH /alerts/{id}/acknowledge -> 403 Forbidden
    status, res = api_call(f"/alerts/{alert_id}/acknowledge", method="PATCH", token=fam_token)
    assert status == 403, f"Expected 403 Forbidden for Family Member on PATCH /acknowledge, got {status}: {res}"
    print("[PASS] Family Member blocked from PATCH /acknowledge (HTTP 403).")

    # 3. Family Member attempts PATCH /alerts/{id}/resolve -> 403 Forbidden
    status, res = api_call(f"/alerts/{alert_id}/resolve", method="PATCH", token=fam_token, data={"resolution_notes": "Family notes"})
    assert status == 403, f"Expected 403 Forbidden for Family Member on PATCH /resolve, got {status}: {res}"
    print("[PASS] Family Member blocked from PATCH /resolve (HTTP 403).")

# ============================================================================
# TEST G: EMERGENCY CONTACT IS NOT A ROLE
# ============================================================================
def test_g_emergency_contact_is_not_a_role():
    print("\n--- Test G: Emergency Contact Is Not A Login Role ---")
    test_email = f"ec_role_{uuid.uuid4().hex[:6]}@test.com"
    test_pass = "Password123!"
    user_id = str(uuid.uuid4())

    with Session(engine) as session:
        user = User(
            id=user_id,
            email=test_email,
            password_hash=hash_password(test_pass),
            first_name="Contact",
            last_name="Person",
            is_active=True
        )
        session.add(user)
        # Assign legacy emergency_contact role_id = 6
        ur = UserRole(user_id=user_id, role_id=6)
        session.add(ur)
        session.commit()

    try:
        auth = login(test_email, test_pass)
        token = auth["access_token"]
        assert auth["role"] == "emergency_contact"

        # Attempt to access /alerts -> 403 Forbidden
        status, res = api_call("/alerts", method="GET", token=token)
        assert status == 403, f"Expected 403 Forbidden for legacy emergency_contact role on /alerts, got {status}: {res}"
        print("[PASS] Legacy emergency_contact role blocked from /alerts (HTTP 403).")

        # Attempt to access Family Portal -> 403 Forbidden
        status, res = api_call("/family/resident-status", method="GET", token=token)
        assert status == 403, f"Expected 403 Forbidden for legacy emergency_contact role on Family Portal, got {status}: {res}"
        print("[PASS] Legacy emergency_contact role blocked from Family Portal (HTTP 403).")
    finally:
        with Session(engine) as session:
            urs = session.exec(select(UserRole).where(UserRole.user_id == user_id)).all()
            for r in urs: session.delete(r)
            u = session.get(User, user_id)
            if u: session.delete(u)
            session.commit()

if __name__ == "__main__":
    print("==========================================================================")
    print("   WIFISENSE GLOBAL / SYSTEM ADMIN ALERT ACCESS & SCOPE VERIFICATION      ")
    print("==========================================================================")
    test_a_global_admin_can_view_care_fall_alert()
    test_b_global_admin_can_acknowledge_fall_alert()
    test_c_global_admin_can_resolve_fall_alert()
    test_d_invalid_lifecycle_remains_blocked()
    test_e_organization_isolation_remains_intact()
    test_f_family_member_cannot_acknowledge_or_resolve()
    test_g_emergency_contact_is_not_a_role()
    print("\n==========================================================================")
    print("      ALL GLOBAL ADMIN ALERT ACCESS & BOUNDARY TESTS PASSED 100%!         ")
    print("==========================================================================")
