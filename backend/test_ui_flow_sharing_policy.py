"""
WIFISENSE SHARING POLICY FRONTEND CONFIGURATION & API INTEGRATION TEST SUITE
===========================================================================
This test suite verifies:
1. Frontend navigation configuration and view authorization matrix in navConfig.js
   (organization_admin removed, facility_manager has sharing_policies and orgadmin).
2. API integration contract for the SharingPolicy UI flow:
   - Facility Manager view & update flow matching UI form payloads
   - Tenant isolation: Facility Manager of Org A CANNOT edit Org B's sharing policy (403)
   - Facility Manager CANNOT list personnel (403)
   - Facility Manager of Org A CANNOT see Org B's audit logs (empty list)
   - Phase 1 restriction: organization_admin CANNOT be assigned via /auth/assign-role (400)
   - Unauthorized roles (Caregiver, Corporate Staff) boundary gating (403)
3. Structured audit logging on policy update.
"""

import os
import json
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import hash_password
from app.models.entities import (
    AuditLog, SharingPolicy, Organization, User, UserRole,
    Building, Floor, Room, Resident, AccessRequest
)

# Environment-configurable endpoints and paths for cross-environment portability
REPO_ROOT = Path(__file__).resolve().parent.parent
NAV_CONFIG_PATH = REPO_ROOT / "frontend" / "src" / "navigation" / "navConfig.js"

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# Test credentials with configurable fallbacks to seeded development users
FM_ADMIN_EMAIL = os.getenv("TEST_FM_ADMIN_EMAIL", "anjali@wifisense.com")
FM_ADMIN_PASSWORD = os.getenv("TEST_FM_ADMIN_PASSWORD", "anjalipassword")

FM_EMAIL = os.getenv("TEST_FM_EMAIL", "elizabeth@wifisense.com")
FM_PASSWORD = os.getenv("TEST_FM_PASSWORD", "elizabethpassword")

CORP_FM_EMAIL = os.getenv("TEST_CORP_FM_EMAIL", "kavitha@wifisense.com")
CORP_FM_PASSWORD = os.getenv("TEST_CORP_FM_PASSWORD", "kavithapassword")

SYSADMIN_EMAIL = os.getenv("TEST_SYSADMIN_EMAIL", "blesson@wifisense.com")
SYSADMIN_PASSWORD = os.getenv("TEST_SYSADMIN_PASSWORD", "blessonpassword")

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
    Validates navigation configuration rules in frontend/src/navigation/navConfig.js:
    - organization_admin is completely removed from BACKEND_ROLES and MATRIX.
    - facility_manager has allowedViews containing sharing_policies and orgadmin.
    - caregiver does not have sharing_policies or orgadmin.
    """
    print("\n--- 1. Testing Frontend Nav Configuration & Gating Matrix ---")
    
    assert NAV_CONFIG_PATH.exists(), f"navConfig.js not found at expected path: {NAV_CONFIG_PATH}"
    with open(NAV_CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "sharing_policies:" in content, "sharing_policies not defined in VIEW_DEFINITIONS in navConfig.js"
    assert '"sharing_policies"' in content, "sharing_policies not mapped in allowedViews"

    import re
    care_matrix = content[content.find("[APP_CONTEXTS.CARE]: {"):]
    
    # 1. Verify organization_admin is NOT in BACKEND_ROLES
    backend_roles_match = re.search(r'export const BACKEND_ROLES = \[(.*?)\];', content, re.DOTALL)
    assert backend_roles_match is not None, "BACKEND_ROLES array not found"
    backend_roles_text = backend_roles_match.group(1)
    assert '"organization_admin"' not in backend_roles_text, "organization_admin must not be in BACKEND_ROLES for Phase 1!"

    # 2. Verify organization_admin is NOT in care_matrix or space_matrix
    assert "organization_admin:" not in content, "organization_admin must not be mapped in navigation matrix!"

    # 3. Verify Caregiver allowedViews does NOT contain orgadmin or sharing_policies
    caregiver_match = re.search(r'caregiver:\s*\{[^}]*allowedViews:\s*(\[[^\]]+\])', care_matrix)
    assert caregiver_match is not None, "caregiver block not found in matrix"
    caregiver_views = caregiver_match.group(1)
    assert "sharing_policies" not in caregiver_views, "Caregiver incorrectly has sharing_policies view!"
    assert "orgadmin" not in caregiver_views, "Caregiver incorrectly has orgadmin view!"

    # 4. Verify Facility Manager allowedViews contains sharing_policies and orgadmin
    fm_match = re.search(r'facility_manager:\s*\{[^}]*allowedViews:\s*(\[[^\]]+\])', care_matrix)
    assert fm_match is not None, "facility_manager block not found in matrix"
    fm_views = fm_match.group(1)
    assert "sharing_policies" in fm_views, "Facility manager missing sharing_policies view!"
    assert "orgadmin" in fm_views, "Facility manager missing orgadmin view!"

    print("[PASS] Navigation matrix verified: FM has view access; Caregiver is strictly blocked; organization_admin is absent.")

def test_facility_manager_view_and_update_flow():
    """
    Tests a Facility Manager loading and updating their facility's SharingPolicy via the UI-flow contract.
    """
    print("\n--- 2. Testing Facility Manager View & Update UI Flow ---")
    
    admin = login(FM_ADMIN_EMAIL, FM_ADMIN_PASSWORD)
    assert admin["role"] == "facility_manager", f"Expected facility_manager role, got {admin['role']}"
    assert admin["application_context"] == "ELDER_CARE"
    token = admin["access_token"]
    
    # Step 1: View - GET /sharing-policies
    status, policies = api_call("/sharing-policies", method="GET", token=token)
    assert status == 200, f"Expected 200, got {status}: {policies}"
    assert len(policies) > 0, "No sharing policies returned for Facility Manager."
    policy = policies[0]
    policy_id = policy["id"]
    print(f"[PASS] Facility Manager successfully viewed {len(policies)} policy(ies). Target policy ID: {policy_id}")
    
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
    print("[PASS] Facility Manager successfully updated policy via UI payload.")
    
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
        assert audit.who_email == FM_ADMIN_EMAIL
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

def test_cross_organization_tenant_isolation_and_gating():
    """
    Tests tenant isolation & Phase 1 negative boundaries:
    1. A facility manager of Org A CANNOT edit Org B's sharing policy (403 Forbidden).
    2. A facility manager of Org A CANNOT see Org B's audit logs (empty list).
    3. A facility manager CANNOT list personnel via GET /users/personnel (403 Forbidden).
    4. Phase 1 block: organization_admin CANNOT be assigned via POST /auth/assign-role (400 Bad Request).
    """
    print("\n--- 3. Testing Cross-Organization Tenant Isolation & Phase 1 Gating ---")
    
    # Get elder-care sharing policy ID and corporate org ID
    with Session(engine) as session:
        care_policy = session.exec(select(SharingPolicy)).first()
        assert care_policy is not None, "No sharing policy found"
        policy_id = care_policy.id
        corp_org = session.exec(select(Organization).where(Organization.type == "CORPORATE")).first()
        assert corp_org is not None, "Corporate organization not found"
        corp_org_id = corp_org.id

    # 1. Facility Manager of Corporate Org attempting to update Elder Care sharing policy -> 403 Forbidden
    corp_fm = login(CORP_FM_EMAIL, CORP_FM_PASSWORD)
    assert corp_fm["role"] == "facility_manager"
    status, res = api_call(
        f"/sharing-policies/{policy_id}",
        method="PUT",
        token=corp_fm["access_token"],
        data={"share_presence": False}
    )
    assert status == 403, f"Cross-org FM should be blocked from editing policy, got {status}: {res}"
    print("[PASS] Cross-organization sharing policy edit rejected with HTTP 403 Forbidden.")

    # 2. Facility Manager of Org A querying audit logs for Org B -> returns empty list
    care_fm = login(FM_ADMIN_EMAIL, FM_ADMIN_PASSWORD)
    status, logs = api_call(f"/auth/audit-logs?organization_id={corp_org_id}", token=care_fm["access_token"])
    assert status == 200, f"Expected 200 from audit logs, got {status}"
    assert logs == [], f"Elder-care FM must receive empty list when querying corporate org logs, got: {logs}"
    print("[PASS] Cross-organization audit log inquiry safely returns empty list.")

    # 3. Facility Manager attempting to access GET /users/personnel -> 403 Forbidden (system_admin only)
    status, res = api_call("/users/personnel", token=care_fm["access_token"])
    assert status == 403, f"Facility Manager must be forbidden from listing personnel, got {status}: {res}"
    print("[PASS] Facility Manager rejected from GET /users/personnel with HTTP 403 Forbidden.")

    # 4. Attempting to assign organization_admin role via POST /auth/assign-role -> 400 Bad Request
    sysadmin = login(SYSADMIN_EMAIL, SYSADMIN_PASSWORD)
    with Session(engine) as session:
        test_user = session.exec(select(User).where(User.email == CAREGIVER_EMAIL)).first()
        target_user_id = test_user.id
    
    status, res = api_call(
        "/auth/assign-role",
        method="POST",
        token=sysadmin["access_token"],
        data={
            "user_id": target_user_id,
            "role": "organization_admin"
        }
    )
    assert status == 400, f"Assigning organization_admin should fail with 400, got {status}: {res}"
    assert "reserved for Phase 2" in str(res), f"Expected clear Phase 2 reservation message, got: {res}"
    print(f"[PASS] Attempting to assign organization_admin rejected with HTTP 400: {res['detail']}.")

    # 5. Access Requests: Scoping and cross-org review boundary
    # a) Caregiver blocked from GET /family/requests -> 403
    cg = login(CAREGIVER_EMAIL, CAREGIVER_PASSWORD)
    status, res = api_call("/family/requests", token=cg["access_token"])
    assert status == 403, f"Caregiver should be blocked from GET /family/requests, got {status}: {res}"

    # b) Corporate FM blocked from GET /family/requests -> 403
    status, res = api_call("/family/requests", token=corp_fm["access_token"])
    assert status == 403, f"Corporate FM should be blocked from GET /family/requests, got {status}: {res}"

    # c) Elder-care FM of Org A gets only Org A requests
    status, care_reqs = api_call("/family/requests", token=care_fm["access_token"])
    assert status == 200, f"Expected 200 from GET /family/requests, got {status}"
    assert len(care_reqs) > 0, "Expected seeded access requests for elder-care org"
    org_a_req_id = care_reqs[0]["id"]

    # d) Create temporary Org B with its own elder-care resident, access request, and FM
    test_org_b_id = "test-org-b-" + uuid.uuid4().hex[:8]
    test_bld_b_id = "test-bld-b-" + uuid.uuid4().hex[:8]
    test_flr_b_id = "test-flr-b-" + uuid.uuid4().hex[:8]
    test_rm_b_id = "test-rm-b-" + uuid.uuid4().hex[:8]
    test_res_b_id = "test-res-b-" + uuid.uuid4().hex[:8]
    test_req_b_id = "test-req-b-" + uuid.uuid4().hex[:8]
    test_fm_b_id = "test-fm-b-" + uuid.uuid4().hex[:8]
    test_fm_b_email = f"fmb_{uuid.uuid4().hex[:6]}@wifisense.com"
    test_fm_b_pass = "TestPass123!"

    with Session(engine) as session:
        org_b = Organization(id=test_org_b_id, name="Test Org B", type="ELDER_CARE")
        session.add(org_b)
        bld_b = Building(id=test_bld_b_id, organization_id=test_org_b_id, name="Building B")
        session.add(bld_b)
        flr_b = Floor(id=test_flr_b_id, building_id=test_bld_b_id, floor_number=1)
        session.add(flr_b)
        rm_b = Room(id=test_rm_b_id, floor_id=test_flr_b_id, name="Room B1", room_type="Resident Bedroom")
        session.add(rm_b)
        res_b = Resident(id=test_res_b_id, room_id=test_rm_b_id, first_name="Resident", last_name="B")
        session.add(res_b)
        session.flush()  # parents first: PostgreSQL enforces the foreign keys SQLite ignores
        req_b = AccessRequest(
            id=test_req_b_id,
            requesting_user_id=target_user_id,
            resident_id=test_res_b_id,
            status="pending"
        )
        session.add(req_b)
        user_b = User(
            id=test_fm_b_id,
            email=test_fm_b_email,
            password_hash=hash_password(test_fm_b_pass),
            first_name="FM",
            last_name="OrgB",
            is_active=True
        )
        session.add(user_b)
        session.commit()

        ur_b = UserRole(
            user_id=test_fm_b_id,
            role_id=3,  # facility_manager
            organization_id=test_org_b_id
        )
        session.add(ur_b)
        session.commit()

    try:
        fm_b = login(test_fm_b_email, test_fm_b_pass)
        assert fm_b["role"] == "facility_manager"

        # e) FM of Org B calling GET /family/requests only sees Org B request
        status, fm_b_reqs = api_call("/family/requests", token=fm_b["access_token"])
        assert status == 200
        req_b_ids = [r["id"] for r in fm_b_reqs]
        assert test_req_b_id in req_b_ids, "Org B FM must see Org B request"
        assert org_a_req_id not in req_b_ids, "Org B FM must NOT see Org A request!"

        # f) FM of Org A calling GET /family/requests does NOT see Org B request
        status, fm_a_reqs = api_call("/family/requests", token=care_fm["access_token"])
        assert status == 200
        req_a_ids = [r["id"] for r in fm_a_reqs]
        assert test_req_b_id not in req_a_ids, "Org A FM must NOT see Org B request!"

        # g) System Admin calling GET /family/requests sees BOTH
        status, sys_reqs = api_call("/family/requests", token=sysadmin["access_token"])
        assert status == 200
        sys_req_ids = [r["id"] for r in sys_reqs]
        assert test_req_b_id in sys_req_ids and org_a_req_id in sys_req_ids, "SysAdmin must see all requests"

        # h) Cross-org negative test: FM of Org B cannot review Org A request -> 403 Forbidden
        status, res = api_call(
            f"/family/requests/{org_a_req_id}",
            method="PATCH",
            token=fm_b["access_token"],
            data={"status": "approved"}
        )
        assert status == 403, f"Cross-org FM review of AccessRequest should fail with 403, got {status}: {res}"
        print("[PASS] Cross-organization access request review rejected with HTTP 403 Forbidden.")
        print("[PASS] Scoped GET /family/requests and cross-org tenant isolation verified.")
    finally:
        # Cleanup test Org B entities
        with Session(engine) as session:
            for entity_type, entity_id in [
                (UserRole, test_fm_b_id),
                (User, test_fm_b_id),
                (AccessRequest, test_req_b_id),
                (Resident, test_res_b_id),
                (Room, test_rm_b_id),
                (Floor, test_flr_b_id),
                (Building, test_bld_b_id),
                (Organization, test_org_b_id),
            ]:
                if entity_type == UserRole:
                    for ur_obj in session.exec(select(UserRole).where(UserRole.user_id == entity_id)).all():
                        session.delete(ur_obj)
                    from app.models.entities import RefreshToken
                    for rt_obj in session.exec(select(RefreshToken).where(RefreshToken.user_id == entity_id)).all():
                        session.delete(rt_obj)
                    session.flush()
                else:
                    obj = session.get(entity_type, entity_id)
                    if obj:
                        session.delete(obj)
                        session.flush()  # children before parents
            session.commit()

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
    test_facility_manager_view_and_update_flow()
    test_cross_organization_tenant_isolation_and_gating()
    test_unauthorized_roles_blocked_flow()
    test_frontend_admin_navigation_routing_separation()
    print("\n==========================================================================")
    print("           ALL SHARING POLICY INTEGRATION TESTS PASSED!                   ")
    print("==========================================================================")
