"""
WIFISENSE SHARING POLICY FRONTEND CONFIGURATION & API INTEGRATION TEST SUITE
===========================================================================
This test suite verifies:
1. Frontend navigation configuration and view authorization matrix in navConfig.js.
2. API integration contract for the SharingPolicy UI flow:
   - Org Admin view & update flow matching UI form payloads
   - Facility Manager read-only view flow (GET allowed, PUT blocked with 403)
   - Unauthorized roles (Caregiver, Corporate Staff) boundary gating
3. Structured audit logging on policy update.

NOTE: This is an automated frontend configuration + API integration test suite.
It does NOT execute real browser DOM rendering or headless browser interactions.
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import AuditLog, SharingPolicy

# Environment-configurable endpoints and paths for cross-environment portability
REPO_ROOT = Path(__file__).resolve().parent.parent
NAV_CONFIG_PATH = REPO_ROOT / "frontend" / "src" / "navigation" / "navConfig.js"

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# Test credentials with configurable fallbacks to seeded development users
ORG_ADMIN_EMAIL = os.getenv("TEST_ORG_ADMIN_EMAIL", "anjali@wifisense.com")
ORG_ADMIN_PASSWORD = os.getenv("TEST_ORG_ADMIN_PASSWORD", "anjalipassword")

FM_EMAIL = os.getenv("TEST_FM_EMAIL", "elizabeth@wifisense.com")
FM_PASSWORD = os.getenv("TEST_FM_PASSWORD", "elizabethpassword")

CAREGIVER_EMAIL = os.getenv("TEST_CAREGIVER_EMAIL", "abhinanth@wifisense.com")
CAREGIVER_PASSWORD = os.getenv("TEST_CAREGIVER_PASSWORD", "abhinanthpassword")

CORP_EMAIL = os.getenv("TEST_CORP_EMAIL", "tomy@wifisense.com")
CORP_PASSWORD = os.getenv("TEST_CORP_PASSWORD", "tomypassword")

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
    Validates the navigation configuration matrix rules in frontend/src/navigation/navConfig.js.
    """
    print("\n--- 1. Testing Frontend Nav Configuration & Gating Matrix ---")
    
    assert NAV_CONFIG_PATH.exists(), f"navConfig.js not found at expected path: {NAV_CONFIG_PATH}"
    with open(NAV_CONFIG_PATH, "r", encoding="utf-8") as f:
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

    # Verify Facility Manager allowedViews contains sharing_policies for read-only viewing
    fm_match = re.search(r'facility_manager:\s*\{[^}]*allowedViews:\s*(\[[^\]]+\])', care_matrix)
    assert fm_match is not None, "facility_manager block not found in matrix"
    fm_views = fm_match.group(1)
    assert "sharing_policies" in fm_views, "Facility manager missing sharing_policies view!"

    print("[PASS] Navigation matrix verified: Org Admin & FM have view access; Caregiver is strictly blocked.")

def test_org_admin_view_and_update_flow():
    """
    Tests an Organization Admin loading and updating their facility's SharingPolicy via the UI-flow contract.
    """
    print("\n--- 2. Testing Org Admin View & Update UI Flow ---")
    
    admin = login(ORG_ADMIN_EMAIL, ORG_ADMIN_PASSWORD)
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
    
    # Step 2: Edit - PUT /sharing-policies/{id} with toggled state matching the UI form
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
        assert audit.who_email == ORG_ADMIN_EMAIL
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
    
    fm = login(FM_EMAIL, FM_PASSWORD)
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
    cg = login(CAREGIVER_EMAIL, CAREGIVER_PASSWORD)
    status, res = api_call("/sharing-policies", method="GET", token=cg["access_token"])
    assert status == 403, f"Caregiver GET /sharing-policies should be 403, got {status}"
    status, res = api_call("/sharing-policies/test-id", method="PUT", token=cg["access_token"], data={})
    assert status == 403, f"Caregiver PUT /sharing-policies should be 403, got {status}"
    print("[PASS] Caregiver blocked from both GET (403) and PUT (403).")
    
    # Corporate Staff
    corp = login(CORP_EMAIL, CORP_PASSWORD)
    status, res = api_call("/sharing-policies", method="GET", token=corp["access_token"])
    assert status == 403, f"Corporate Staff GET /sharing-policies should be 403, got {status}"
    status, res = api_call("/sharing-policies/test-id", method="PUT", token=corp["access_token"], data={})
    assert status == 403, f"Corporate Staff PUT /sharing-policies should be 403, got {status}"
    print("[PASS] Corporate Staff blocked from both GET (403) and PUT (403).")

def test_frontend_admin_navigation_routing_separation():
    """
    Validates that App.jsx routes 'orgadmin' to OrgAdminView and 'sharing_policies' to SharingPolicyManager
    in distinct, uncoupled rendering branches rather than a shared compound conditional.
    """
    print("\n--- 5. Testing Frontend Admin Navigation Routing Separation ---")
    app_jsx_path = REPO_ROOT / "frontend" / "src" / "App.jsx"
    assert app_jsx_path.exists(), f"App.jsx not found at: {app_jsx_path}"
    with open(app_jsx_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Verify SharingPolicyManager is imported
    assert "import SharingPolicyManager from" in content, "SharingPolicyManager not imported in App.jsx"

    # 2. Verify compound conditional is eliminated
    assert 'currentView === "orgadmin" || currentView === "sharing_policies"' not in content, \
        "Coupled compound conditional still exists in App.jsx!"

    # 3. Verify separate branch for orgadmin renders OrgAdminView
    import re
    orgadmin_branch = re.search(r'currentView === ["\']orgadmin["\'].*?<OrgAdminView', content, re.DOTALL)
    assert orgadmin_branch is not None, "currentView === 'orgadmin' does not render <OrgAdminView"

    # 4. Verify separate branch for sharing_policies renders SharingPolicyManager
    sharing_branch = re.search(r'currentView === ["\']sharing_policies["\'].*?<SharingPolicyManager', content, re.DOTALL)
    assert sharing_branch is not None, "currentView === 'sharing_policies' does not render <SharingPolicyManager"

    print("[PASS] Navigation routing separation verified: 'orgadmin' -> OrgAdminView, 'sharing_policies' -> SharingPolicyManager.")

if __name__ == "__main__":
    print("==========================================================================")
    print("  WIFISENSE SHARING POLICY FRONTEND CONFIG & API INTEGRATION TEST SUITE   ")
    print("==========================================================================")
    test_frontend_nav_matrix_rules()
    test_org_admin_view_and_update_flow()
    test_facility_manager_view_only_flow()
    test_unauthorized_roles_blocked_flow()
    test_frontend_admin_navigation_routing_separation()
    print("\n==========================================================================")
    print("           ALL SHARING POLICY INTEGRATION TESTS PASSED!                   ")
    print("==========================================================================")
