import json
import urllib.request
import urllib.error
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import AuditLog, SharingPolicy

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

def test_frontend_nav_matrix_rules():
    """
    Validates the navigation configuration matrix rules mirroring the frontend navConfig.js.
    """
    print("\n--- 1. Testing Frontend Nav Configuration & Gating Matrix ---")
    
    # Read navConfig.js to verify rules are correctly defined
    with open("d:/Wifisense/frontend/src/navigation/navConfig.js", "r", encoding="utf-8") as f:
        content = f.read()

    assert "sharing_policies:" in content, "sharing_policies not defined in VIEW_DEFINITIONS in navConfig.js"
    assert '"sharing_policies"' in content, "sharing_policies not mapped in allowedViews"

    import re
    care_matrix = content[content.find("[APP_CONTEXTS.CARE]: {"):]
    
    # Verify Caregiver allowedViews does NOT contain orgadmin or sharing_policies
    caregiver_match = re.search(r'caregiver:\s*\{[^}]*allowedViews:\s*(\[[^\]]+\])', care_matrix)
    assert caregiver_match is not None, "caregiver block not found in matrix"
    caregiver_views = caregiver_match.group(1)
    assert "sharing_policies" not in caregiver_views, "Caregiver incorrectly has sharing_policies view!"
    assert "orgadmin" not in caregiver_views, "Caregiver incorrectly has orgadmin view!"

    # Verify Organization Admin allowedViews contains both
    org_admin_match = re.search(r'organization_admin:\s*\{[^}]*allowedViews:\s*(\[[^\]]+\])', care_matrix)
    assert org_admin_match is not None, "organization_admin block not found in matrix"
    org_admin_views = org_admin_match.group(1)
    assert "sharing_policies" in org_admin_views, "Org admin missing sharing_policies view!"
    assert "orgadmin" in org_admin_views, "Org admin missing orgadmin view!"

    # Verify Facility Manager allowedViews contains both for view capability
    fm_match = re.search(r'facility_manager:\s*\{[^}]*allowedViews:\s*(\[[^\]]+\])', care_matrix)
    assert fm_match is not None, "facility_manager block not found in matrix"
    fm_views = fm_match.group(1)
    assert "sharing_policies" in fm_views, "Facility manager missing sharing_policies view!"

    print("[PASS] Navigation matrix verified: Org Admin & FM have view access; Caregiver is strictly blocked.")

def test_org_admin_view_and_update_flow():
    """
    Tests an Organization Admin loading and updating their facility's SharingPolicy via the UI flow.
    """
    print("\n--- 2. Testing Org Admin View & Update UI Flow ---")
    
    admin = login("anjali@wifisense.com", "anjalipassword")
    assert admin["role"] == "organization_admin"
    assert admin["application_context"] == "ELDER_CARE"
    token = admin["access_token"]
    
    # Step 1: View - GET /sharing-policies
    status, policies = api_call("/sharing-policies", method="GET", token=token)
    assert status == 200, f"Expected 200, got {status}: {policies}"
    assert len(policies) > 0, "No sharing policies returned for Org Admin."
    policy = policies[0]
    policy_id = policy["id"]
    print(f"[PASS] Org Admin successfully viewed {len(policies)} policy(ies). Target policy ID: {policy_id}")
    
    orig_presence = policy["share_presence"]
    orig_threshold = policy["share_alert_severity_threshold"]
    
    # Step 2: Edit - PUT /sharing-policies/{id} with toggled state
    new_presence = not orig_presence
    new_threshold = "CRITICAL" if orig_threshold != "CRITICAL" else "LOW"
    
    print(f"Updating policy: share_presence -> {new_presence}, severity_threshold -> {new_threshold}...")
    status, update_res = api_call(
        f"/sharing-policies/{policy_id}",
        method="PUT",
        token=token,
        data={
            "share_presence": new_presence,
            "share_alert_severity_threshold": new_threshold
        }
    )
    assert status == 200, f"Expected 200, got {status}: {update_res}"
    assert update_res["share_presence"] == new_presence
    assert update_res["share_alert_severity_threshold"] == new_threshold
    print("[PASS] Org Admin successfully updated policy via UI payload.")
    
    # Step 3: Verify Persistence via subsequent GET
    status, refreshed_policies = api_call("/sharing-policies", method="GET", token=token)
    refreshed = next(p for p in refreshed_policies if p["id"] == policy_id)
    assert refreshed["share_presence"] == new_presence
    assert refreshed["share_alert_severity_threshold"] == new_threshold
    print("[PASS] Policy changes persisted and verified on reload.")
    
    # Step 4: Verify Audit Logging
    with Session(engine) as session:
        audit = session.exec(
            select(AuditLog)
            .where(
                AuditLog.resource_id == policy_id,
                AuditLog.what_action == "SHARING_POLICY_UPDATED"
            )
            .order_by(AuditLog.created_at.desc())
        ).first()
        assert audit is not None, "Audit log not recorded for policy update."
        assert audit.who_email == "anjali@wifisense.com"
        assert audit.result == "SUCCESS"
        print(f"[PASS] Audit log verified: {audit.what_action} by {audit.who_email}.")

    # Restore original settings
    api_call(
        f"/sharing-policies/{policy_id}",
        method="PUT",
        token=token,
        data={
            "share_presence": orig_presence,
            "share_alert_severity_threshold": orig_threshold
        }
    )
    print("[PASS] Restored original policy values.")

def test_facility_manager_view_only_flow():
    """
    Tests Facility Manager: Can view policies (200), but cannot modify (403).
    """
    print("\n--- 3. Testing Facility Manager Read-Only UI Flow ---")
    
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    assert fm["role"] == "facility_manager"
    token = fm["access_token"]
    
    # Step 1: View - GET /sharing-policies succeeds
    status, policies = api_call("/sharing-policies", method="GET", token=token)
    assert status == 200, f"Facility Manager should be able to view policies, got {status}"
    assert len(policies) > 0
    policy_id = policies[0]["id"]
    print(f"[PASS] Facility Manager successfully viewed {len(policies)} policy(ies).")
    
    # Step 2: Attempt Edit - PUT /sharing-policies/{id} must be blocked with 403 Forbidden
    status, res = api_call(
        f"/sharing-policies/{policy_id}",
        method="PUT",
        token=token,
        data={"share_presence": False}
    )
    assert status == 403, f"Facility Manager should be blocked from editing policy, got {status}: {res}"
    print("[PASS] Facility Manager edit attempt correctly rejected with HTTP 403 Forbidden.")

def test_unauthorized_roles_blocked_flow():
    """
    Tests Caregiver and Corporate Staff: Strictly blocked from viewing and editing sharing policies.
    """
    print("\n--- 4. Testing Unauthorized Roles Blocked Flow ---")
    
    # Caregiver
    cg = login("abhinanth@wifisense.com", "abhinanthpassword")
    status, res = api_call("/sharing-policies", method="GET", token=cg["access_token"])
    assert status == 403, f"Caregiver GET /sharing-policies should be 403, got {status}"
    status, res = api_call("/sharing-policies/test-id", method="PUT", token=cg["access_token"], data={})
    assert status == 403, f"Caregiver PUT /sharing-policies should be 403, got {status}"
    print("[PASS] Caregiver blocked from both GET (403) and PUT (403).")
    
    # Corporate Staff
    corp = login("tomy@wifisense.com", "tomypassword")
    status, res = api_call("/sharing-policies", method="GET", token=corp["access_token"])
    assert status == 403, f"Corporate Staff GET /sharing-policies should be 403, got {status}"
    status, res = api_call("/sharing-policies/test-id", method="PUT", token=corp["access_token"], data={})
    assert status == 403, f"Corporate Staff PUT /sharing-policies should be 403, got {status}"
    print("[PASS] Corporate Staff blocked from both GET (403) and PUT (403).")

if __name__ == "__main__":
    print("==================================================")
    print("    WIFISENSE SHARING POLICY UI FLOW TEST SUITE   ")
    print("==================================================")
    test_frontend_nav_matrix_rules()
    test_org_admin_view_and_update_flow()
    test_facility_manager_view_only_flow()
    test_unauthorized_roles_blocked_flow()
    print("\n==================================================")
    print("       ALL SHARING POLICY UI TESTS PASSED!        ")
    print("==================================================")
