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
    assert family["role"] == "emergency_contact", f"Expected emergency_contact, got {family['role']}"
    assert family["application_context"] == "ELDER_CARE", f"Expected ELDER_CARE, got {family['application_context']}"
    print("[PASS] Family Member login context verified (ELDER_CARE)")

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
        data={"room_id": target_corp_room_id, "first_name": "Test", "last_name": "Resident"}
    )
    assert status == 403, f"Expected 403 Forbidden on corporate resident creation, got {status}: {post_res}"
    print("[PASS] Corporate facility manager attempting POST /residents correctly received 403 Forbidden")

    # 4. Test SharingPolicy Endpoints (Fix 5)
    print("\n--- 4. Testing SharingPolicy Endpoints (Fix 5) ---")
    # Corporate user GET /sharing-policies -> 403
    status, sp_corp = api_call("/sharing-policies", method="GET", token=corp_staff['access_token'])
    assert status == 403, f"Expected 403, got {status}: {sp_corp}"
    print("[PASS] Corporate user calling GET /sharing-policies received 403 Forbidden")

    # Caregiver GET /sharing-policies -> 403 (role caregiver not allowed)
    status, sp_cg = api_call("/sharing-policies", method="GET", token=caregiver['access_token'])
    assert status == 403, f"Expected 403, got {status}: {sp_cg}"
    print("[PASS] Caregiver calling GET /sharing-policies received 403 Forbidden")

    # Caregiver PUT /sharing-policies/dummy -> 403
    status, sp_cg_put = api_call("/sharing-policies/some-id", method="PUT", token=caregiver['access_token'], data={"share_presence": False})
    assert status == 403, f"Expected 403, got {status}: {sp_cg_put}"
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
    print(f"[PASS] Family member GET /family/resident-status returned linked resident: {fam_data['resident']['first_name']}")

    print("\n>>> ALL 12 DIRECT API BOUNDARY TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
