import json
import urllib.request
import urllib.error

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

def run_tests():
    print("=== RUNNING BACKEND BOUNDARY TESTS ===")
    
    # 1. Test Login Contexts (Fix 1)
    print("\n--- 1. Testing Deterministic Context Pinning (Fix 1) ---")
    sysadmin = login("blesson@wifisense.com", "blessonpassword")
    assert sysadmin["role"] == "system_admin", f"Expected system_admin, got {sysadmin['role']}"
    assert sysadmin["application_context"] == "SYSTEM", f"Expected SYSTEM, got {sysadmin['application_context']}"
    assert sysadmin["is_system_admin"] is True
    print("[PASS] System Admin login context verified (SYSTEM, is_system_admin=True)")

    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")
    assert corp_fm["role"] == "facility_manager", f"Expected facility_manager, got {corp_fm['role']}"
    assert corp_fm["application_context"] == "CORPORATE", f"Expected CORPORATE, got {corp_fm['application_context']}"
    assert corp_fm["is_system_admin"] is False
    print("[PASS] Corporate Facility Manager login context verified (CORPORATE)")

    corp_staff = login("tomy@wifisense.com", "tomypassword")
    assert corp_staff["role"] == "corporate_staff", f"Expected corporate_staff, got {corp_staff['role']}"
    assert corp_staff["application_context"] == "CORPORATE", f"Expected CORPORATE, got {corp_staff['application_context']}"
    print("[PASS] Corporate Staff login context verified (CORPORATE)")

    caregiver = login("abhinanth@wifisense.com", "abhinanthpassword")
    assert caregiver["role"] == "caregiver", f"Expected caregiver, got {caregiver['role']}"
    assert caregiver["application_context"] == "ELDER_CARE", f"Expected ELDER_CARE, got {caregiver['application_context']}"
    print("[PASS] Caregiver login context verified (ELDER_CARE)")

    care_fm = login("elizabeth@wifisense.com", "elizabethpassword")
    assert care_fm["role"] == "facility_manager", f"Expected facility_manager, got {care_fm['role']}"
    assert care_fm["application_context"] == "ELDER_CARE", f"Expected ELDER_CARE, got {care_fm['application_context']}"
    print("[PASS] Elder-care Facility Manager login context verified (ELDER_CARE)")

    family = login("john@wifisense.com", "johnpassword")
    assert family["role"] == "family_member", f"Expected family_member, got {family['role']}"
    assert family["application_context"] == "ELDER_CARE", f"Expected ELDER_CARE, got {family['application_context']}"
    print("[PASS] Family Member login context verified (ELDER_CARE, role=family_member)")

    # 2. Test Scoped Reads (Fix 3 - Option A)
    print("\n--- 2. Testing Scoped Reads (Fix 3 - Option A) ---")
    status, res = api_call("/residents", method="GET", token=corp_staff['access_token'])
    assert status == 200, f"Expected 200, got {status}"
    assert res == [], f"Expected empty list for corporate user on /residents, got {res}"
    print("[PASS] Corporate user GET /residents returns empty list [] via scope isolation")

    status, care_residents = api_call("/residents", method="GET", token=caregiver['access_token'])
    assert status == 200, f"Expected 200, got {status}"
    assert len(care_residents) > 0, "Expected elder care residents for caregiver"
    print(f"[PASS] Caregiver GET /residents returns {len(care_residents)} residents")

    # 3. Test POST /residents Org Type Check (Fix 4)
    print("\n--- 3. Testing POST /residents Org Type Check (Fix 4) ---")
    status, corp_rooms = api_call("/rooms", method="GET", token=corp_fm['access_token'])
    assert status == 200 and len(corp_rooms) > 0, "Expected rooms for corporate FM"
    target_corp_room_id = corp_rooms[0]["id"]

    status, post_res = api_call(
        "/residents",
        method="POST",
        token=corp_fm['access_token'],
        data={
            "room_id": target_corp_room_id,
            "first_name": "Test",
            "last_name": "Resident",
            "date_of_birth": "1940-01-01"
        }
    )
    assert status == 403, f"Expected 403 Forbidden on corporate resident creation, got {status}: {post_res}"
    print("[PASS] Corporate facility manager attempting POST /residents correctly received 403 Forbidden")

    # 4. Test SharingPolicy Endpoints (Fix 5)
    print("\n--- 4. Testing SharingPolicy Endpoints (Fix 5) ---")
    # Corporate user GET /sharing-policies -> 403
    status, sp_corp = api_call("/sharing-policies", method="GET", token=corp_staff['access_token'])
    assert status == 403, f"Expected 403, got {status}: {sp_corp}"
    print("[PASS] Corporate user calling GET /sharing-policies received 403 Forbidden")

    # Caregiver GET /sharing-policies -> 403
    status, sp_care = api_call("/sharing-policies", method="GET", token=caregiver['access_token'])
    assert status == 403, f"Expected 403, got {status}: {sp_care}"
    print("[PASS] Caregiver calling GET /sharing-policies received 403 Forbidden")

    # Caregiver PUT /sharing-policies/{id} -> 403
    status, sp_care_put = api_call("/sharing-policies/dummy", method="PUT", token=caregiver['access_token'], data={})
    assert status == 403, f"Expected 403, got {status}: {sp_care_put}"
    print("[PASS] Caregiver calling PUT /sharing-policies/{id} received 403 Forbidden")

    # Elder-care FM GET /sharing-policies -> 200
    status, policies = api_call("/sharing-policies", method="GET", token=care_fm['access_token'])
    assert status == 200, f"Expected 200, got {status}: {policies}"
    assert len(policies) > 0, "Expected sharing policies for elder-care org"
    print(f"[PASS] Elder-care FM calling GET /sharing-policies received 200 OK ({len(policies)} policies)")

    # System Admin PUT /sharing-policies/{id} -> 200
    target_policy_id = policies[0]["id"]
    status, sp_update = api_call(
        f"/sharing-policies/{target_policy_id}",
        method="PUT",
        token=sysadmin['access_token'],
        data={"share_presence": True, "share_alert_severity_threshold": "HIGH"}
    )
    assert status == 200, f"Expected 200, got {status}: {sp_update}"
    print("[PASS] System Admin PUT /sharing-policies/{id} succeeded with 200 OK")

    # 5. Test Family Portal Boundaries
    print("\n--- 5. Testing Family Portal Boundaries ---")
    # Corporate user calling /family/resident-status -> 403
    status, fam_corp = api_call("/family/resident-status", method="GET", token=corp_staff['access_token'])
    assert status == 403, f"Expected 403, got {status}: {fam_corp}"
    print("[PASS] Corporate user calling GET /family/resident-status received 403 Forbidden")

    # Corporate user calling POST /family/requests -> 403
    status, fam_corp_post = api_call("/family/requests", method="POST", token=corp_staff['access_token'], data={"resident_id": "dummy"})
    assert status == 403, f"Expected 403, got {status}: {fam_corp_post}"
    print("[PASS] Corporate user calling POST /family/requests received 403 Forbidden")

    # Caregiver calling PATCH /family/requests/dummy -> 403
    status, care_patch = api_call("/family/requests/dummy", method="PATCH", token=caregiver['access_token'], data={"status": "org_approved"})
    assert status == 403, f"Expected 403, got {status}: {care_patch}"
    print("[PASS] Caregiver calling PATCH /family/requests/{id} received 403 Forbidden")

    # Legitimate Family Member calling /family/resident-status -> 200
    status, fam_data = api_call("/family/resident-status", method="GET", token=family['access_token'])
    assert status == 200, f"Expected 200, got {status}: {fam_data}"
    assert fam_data["linked"] is True, f"Expected linked resident for John, got {fam_data}"
    assert fam_data["has_active_subscription"] is True
    print(f"[PASS] Family member GET /family/resident-status returned linked resident: {fam_data['resident']['first_name']}")

    # 6. Test Legacy emergency_contact Role Rejection (B4)
    print("\n--- 6. Testing Legacy emergency_contact Role Access Rejection (B4) ---")
    # Temporarily create/assign a user with role_id 6 (legacy emergency_contact) in the DB
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.entities import User, UserRole, FamilySubscription
    from app.core.security import hash_password
    import uuid

    legacy_email = f"legacy.ec.{uuid.uuid4().hex[:6]}@test.com"
    legacy_user_id = str(uuid.uuid4())
    with Session(engine) as db:
        legacy_u = User(
            id=legacy_user_id,
            email=legacy_email,
            password_hash=hash_password("legacypass"),
            first_name="Legacy",
            last_name="Contact",
            is_active=True
        )
        db.add(legacy_u)
        db.add(UserRole(user_id=legacy_user_id, role_id=6))
        db.commit()

    try:
        legacy_token_res = login(legacy_email, "legacypass")
        legacy_token = legacy_token_res["access_token"]
        assert legacy_token_res["role"] == "emergency_contact", f"Expected emergency_contact, got {legacy_token_res['role']}"

        # Attempt GET /family/resident-status -> MUST BE 403 Forbidden
        status, ec_res_status = api_call("/family/resident-status", method="GET", token=legacy_token)
        assert status == 403, f"Expected 403 for legacy emergency_contact accessing resident-status, got {status}"
        print("[PASS] Legacy emergency_contact role blocked from GET /family/resident-status (HTTP 403)")

        # Attempt POST /family/connections -> MUST BE 403 Forbidden
        status, ec_conn_post = api_call("/family/connections", method="POST", token=legacy_token, data={"resident_id": "dummy", "relationship": "Friend"})
        assert status == 403, f"Expected 403 for legacy emergency_contact submitting connection, got {status}"
        print("[PASS] Legacy emergency_contact role blocked from POST /family/connections (HTTP 403)")

        # Attempt GET /family/subscriptions -> MUST BE 403 Forbidden
        status, ec_subs = api_call("/family/subscriptions", method="GET", token=legacy_token)
        assert status == 403, f"Expected 403 for legacy emergency_contact listing subscriptions, got {status}"
        print("[PASS] Legacy emergency_contact role blocked from GET /family/subscriptions (HTTP 403)")
    finally:
        with Session(engine) as db:
            db.exec(sa_delete := select(UserRole).where(UserRole.user_id == legacy_user_id))
            for ur in db.exec(sa_delete).all():
                db.delete(ur)
            u_to_del = db.get(User, legacy_user_id)
            if u_to_del:
                db.delete(u_to_del)
            db.commit()

    # 7. Test Explicit Subscription Gating (B5)
    print("\n--- 7. Testing Explicit Subscription Gating Scenarios (B5) ---")
    # Query John's subscription using family token
    status, my_subs = api_call("/family/subscriptions", method="GET", token=family['access_token'])
    assert status == 200 and len(my_subs) > 0, f"Expected subscriptions for John: {my_subs}"
    sub_id = my_subs[0]["id"]

    try:
        # Scenario A: ACTIVE subscription -> Receives full real-time resident telemetry
        status, act_data = api_call("/family/resident-status", method="GET", token=family['access_token'])
        assert status == 200
        assert act_data["has_active_subscription"] is True
        assert "presence_status" in act_data
        assert "recent_activity_history" in act_data
        assert "current_activity" in act_data
        print("[PASS] ACTIVE subscription: Full real-time resident telemetry accessible.")

        # Scenario B: PENDING subscription -> NO real-time resident data
        status, _ = api_call(f"/family/subscriptions/{sub_id}", method="PATCH", token=care_fm['access_token'], data={"status": "PENDING"})
        assert status == 200
        status, pend_data = api_call("/family/resident-status", method="GET", token=family['access_token'])
        assert status == 200
        assert pend_data["has_active_subscription"] is False
        assert pend_data["subscription_status"] == "PENDING"
        assert "presence_status" not in pend_data
        assert "recent_activity_history" not in pend_data
        assert "current_activity" not in pend_data
        assert "Active family subscription required" in pend_data["reason"]
        print("[PASS] PENDING subscription: Real-time telemetry withheld; subscription status communicated.")

        # Scenario C: EXPIRED subscription -> NO real-time resident data
        status, _ = api_call(f"/family/subscriptions/{sub_id}", method="PATCH", token=care_fm['access_token'], data={"status": "EXPIRED"})
        assert status == 200
        status, exp_data = api_call("/family/resident-status", method="GET", token=family['access_token'])
        assert status == 200
        assert exp_data["has_active_subscription"] is False
        assert exp_data["subscription_status"] == "EXPIRED"
        assert "presence_status" not in exp_data
        assert "recent_activity_history" not in exp_data
        assert "current_activity" not in exp_data
        assert "Active family subscription required" in exp_data["reason"]
        print("[PASS] EXPIRED subscription: Real-time telemetry withheld; subscription status communicated.")

        # Scenario D: SUSPENDED subscription -> NO real-time resident data
        status, _ = api_call(f"/family/subscriptions/{sub_id}", method="PATCH", token=care_fm['access_token'], data={"status": "SUSPENDED"})
        assert status == 200
        status, susp_data = api_call("/family/resident-status", method="GET", token=family['access_token'])
        assert status == 200
        assert susp_data["has_active_subscription"] is False
        assert susp_data["subscription_status"] == "SUSPENDED"
        assert "presence_status" not in susp_data
        assert "recent_activity_history" not in susp_data
        assert "current_activity" not in susp_data
        assert "Active family subscription required" in susp_data["reason"]
        print("[PASS] SUSPENDED subscription: Real-time telemetry withheld; subscription status communicated.")
    finally:
        # Restore John's subscription back to ACTIVE
        api_call(f"/family/subscriptions/{sub_id}", method="PATCH", token=care_fm['access_token'], data={"status": "ACTIVE"})

    # Verify restored state
    status, restored_data = api_call("/family/resident-status", method="GET", token=family['access_token'])
    assert status == 200
    assert restored_data["has_active_subscription"] is True
    print("[PASS] Restored ACTIVE subscription: Real-time telemetry restored successfully.")

    print("\n>>> ALL 16 DIRECT API BOUNDARY & SUBSCRIPTION TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
