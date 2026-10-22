"""
Organization-scoped audit logs.

Before: any organization administrator could read the audit trail of EVERY organization (e-mails, IPs, actions).
Now: an organization administrator sees only events attributed to their own organization; events that cannot be
attributed to one organization (for example a login attempt with an unknown e-mail) are system-administrator only.

Runs against a live seeded server (API_BASE) and the same DATABASE_URL. The migration back-fill is tested in a
subprocess against a temporary database built at the previous revision.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

from sqlmodel import Session, select

from app.core.audit import record_audit_event, resolve_organization
from app.core.database import engine
from app.models.entities import AuditLog, Organization, User

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
BACKEND = os.path.dirname(os.path.abspath(__file__))


def api_call(endpoint, method="GET", data=None, token=None):
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(f"{API_BASE}{endpoint}", data=req_data, method=method)
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
            return e.code, json.loads(body)
        except Exception:
            return e.code, body


def login(email, password, expect=200):
    status, res = api_call("/auth/login", "POST", {"email": email, "password": password})
    assert status == expect, f"login {email}: {status} {res}"
    return res.get("access_token") if status == 200 else None


def run_tests():
    print("=== RUNNING ORGANIZATION-SCOPED AUDIT LOG TESTS ===")
    with Session(engine) as session:
        care_org = session.exec(select(Organization).where(Organization.type == "ELDER_CARE")).first().id
        corp_org = session.exec(select(Organization).where(Organization.type == "CORPORATE")).first().id
        mathew_id = session.exec(select(User).where(User.email == "mathew.varghese@wifisense.com")).first().id

    # ---------------------------------------------------------------- generate activity in both organizations
    care_admin = login("anjali@wifisense.com", "anjalipassword")
    corp_admin = login("kavitha@wifisense.com", "kavithapassword")
    sysadmin = login("blesson@wifisense.com", "blessonpassword")
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")
    doctor = login("mathew.varghese@wifisense.com", "doctorpassword")
    login("anjali@wifisense.com", "wrong-password", expect=401)           # known user, failed
    login("nobody-audit-test@example.com", "wrong-password", expect=401)  # unknown e-mail
    status, mine = api_call("/medical/my-residents", token=doctor)         # doctor activity (no org on the role)
    assert status == 200
    status, rec = api_call(f"/medical/residents/{mine[0]['id']}/record", token=doctor)
    assert status == 200

    def trail(token, suffix=""):
        status, rows = api_call(f"/auth/audit-logs?limit=500{suffix}", token=token)
        assert status == 200, f"{status} {rows}"
        return rows

    # ---------------------------------------------------------------- 1. each organization sees only its own trail
    print("\n--- 1. Organization administrators see only their own organization ---")
    care_rows = trail(care_admin)
    assert care_rows, "care admin sees nothing"
    assert all(r["organization_id"] == care_org for r in care_rows), "Care admin sees events of another organization!"
    assert any(r["what_action"] == "AUTH_LOGIN_SUCCESS" and r["who_email"] == "anjali@wifisense.com" for r in care_rows)
    assert not any((r["who_email"] or "").startswith(("kavitha@", "abhinand@")) for r in care_rows), \
        "Corporate users' activity is visible to the elder-care admin"
    print(f"[PASS] Elder-care admin: {len(care_rows)} events, all attributed to the elder-care organization.")

    corp_rows = trail(corp_admin)
    assert corp_rows and all(r["organization_id"] == corp_org for r in corp_rows), "Corporate admin sees another organization!"
    assert any(r["who_email"] == "kavitha@wifisense.com" for r in corp_rows)
    assert not any((r["who_email"] or "").startswith(("anjali@", "mathew.")) for r in corp_rows), \
        "Elder-care activity is visible to the corporate admin"
    print(f"[PASS] Corporate admin: {len(corp_rows)} events, all attributed to the corporate organization.")

    # ---------------------------------------------------------------- 2. unattributable events are system-admin only
    print("\n--- 2. Unattributable events are system-administrator only ---")
    assert not any(r["who_email"] == "nobody-audit-test@example.com" for r in care_rows + corp_rows)
    sys_rows = trail(sysadmin)
    unknown = [r for r in sys_rows if r["who_email"] == "nobody-audit-test@example.com"]
    assert unknown and unknown[0]["organization_id"] is None
    assert {care_org, corp_org} <= {r["organization_id"] for r in sys_rows}, "System admin must see both organizations"
    print("[PASS] A login attempt with an unknown e-mail is invisible to organization admins and visible to the system admin.")

    failed = [r for r in care_rows if r["what_action"] == "AUTH_LOGIN_FAILED" and r["who_email"] == "anjali@wifisense.com"]
    assert failed, "A failed login for a known user must be attributed to that user's organization"
    print("[PASS] A failed login for a known user is attributed to that user's organization (found by e-mail).")

    # ---------------------------------------------------------------- 3. doctors have no organization on their role
    print("\n--- 3. Doctor activity is attributed through the doctor's approving organization ---")
    doc_care = [r for r in care_rows if r["who_email"] == "mathew.varghese@wifisense.com"]
    assert any(r["what_action"] == "MEDICAL_RECORD_VIEWED" for r in doc_care), "Doctor's record view missing from the care trail"
    assert not any(r["who_email"] == "mathew.varghese@wifisense.com" for r in corp_rows)
    print("[PASS] A doctor's record views appear in the approving organization's trail and nowhere else.")

    # ---------------------------------------------------------------- 4. filters and limits
    print("\n--- 4. Filters cannot be used to look at another organization ---")
    status, rows = api_call(f"/auth/audit-logs?organization_id={corp_org}", token=care_admin)
    assert status == 200 and rows == [], "organization_id filter leaked another organization"
    rows = trail(care_admin, f"&organization_id={care_org}")
    assert rows and all(r["organization_id"] == care_org for r in rows)
    rows = trail(sysadmin, f"&organization_id={corp_org}")
    assert rows and all(r["organization_id"] == corp_org for r in rows)
    rows = trail(care_admin, "&action=AUTH_LOGIN_SUCCESS")
    assert rows and all(r["what_action"] == "AUTH_LOGIN_SUCCESS" and r["organization_id"] == care_org for r in rows)
    status, rows = api_call("/auth/audit-logs?limit=100000", token=care_admin)
    assert status == 200 and len(rows) <= 500
    status, rows = api_call("/auth/audit-logs?limit=0", token=sysadmin)
    assert status == 200 and len(rows) == 1, "limit is clamped to at least 1"
    print("[PASS] The organization filter cannot widen access; action filter stays scoped; limit is clamped to 1..500.")

    # ---------------------------------------------------------------- 5. who may read the trail at all
    print("\n--- 5. Roles ---")
    caregiver = login("abhinanth@wifisense.com", "abhinanthpassword")
    for name, tok in (("caregiver", caregiver), ("doctor", doctor)):
        status, res = api_call("/auth/audit-logs", token=tok)
        assert status == 403, f"{name} read the audit trail: {status}"
    status, res = api_call("/auth/audit-logs")
    assert status == 401
    print("[PASS] Caregivers, doctors and anonymous callers are refused.")

    # ---------------------------------------------------------------- 6. attribution rules (in-process)
    print("\n--- 6. Attribution rules ---")
    with Session(engine) as session:
        care_admin_id = session.exec(select(User).where(User.email == "anjali@wifisense.com")).first().id
        sys_id = session.exec(select(User).where(User.email == "blesson@wifisense.com")).first().id
        assert resolve_organization(session, care_admin_id, None, {"organization_id": corp_org}) == care_org, \
            "The actor's organization must win: a denied cross-organization attempt belongs to the actor's trail"
        assert resolve_organization(session, sys_id, None, {"organization_id": corp_org}) == corp_org, \
            "An actor without an organization falls back to the organization named in the event"
        assert resolve_organization(session, sys_id, None, {"organization_id": 7}) is None
        assert resolve_organization(session, None, "nobody-audit-test@example.com", None) is None
        assert resolve_organization(session, mathew_id, None, None) == care_org
        row = record_audit_event(session, "TEST_EVENT", "TEST", who_user_id=care_admin_id, organization_id=corp_org)
        assert row.organization_id == corp_org, "An explicit organization overrides resolution"
        session.delete(session.get(AuditLog, row.id))
        session.commit()
    print("[PASS] Actor's organization wins; no-org actors use the event's organization; unknown stays unattributed.")

    # ---------------------------------------------------------------- 7. migration back-fill
    print("\n--- 7. Migration back-fills existing rows safely ---")
    tmp = tempfile.mkdtemp(prefix="audit_mig_")
    db_path = os.path.join(tmp, "legacy.db")
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db_path}", SEED_DEMO_DATA="0")

    def alembic(*args):
        out = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, capture_output=True, text=True)
        assert out.returncode == 0, f"alembic {args} failed:\n{out.stdout}\n{out.stderr}"

    alembic("upgrade", "c4a8e2d1f9b3")      # the schema BEFORE audit_logs.organization_id
    con = sqlite3.connect(db_path)

    def insert(table, **values):
        cols = con.execute(f"PRAGMA table_info({table})").fetchall()
        row = dict(values)
        for _, name, ctype, notnull, default, _pk in cols:
            if name in row or not notnull or default is not None:
                continue
            t = (ctype or "").upper()
            row[name] = 1 if ("INT" in t or "BOOL" in t) else ("2026-10-01 00:00:00" if "DATE" in t else "x")
        con.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' * len(row))})", list(row.values()))

    insert("organizations", id="o-a", name="Org A", type="ELDER_CARE")
    insert("organizations", id="o-b", name="Org B", type="CORPORATE")
    insert("users", id="u-single", email="single@example.com", password_hash="x", first_name="S", last_name="S")
    insert("users", id="u-multi", email="multi@example.com", password_hash="x", first_name="M", last_name="M")
    insert("users", id="u-doc", email="doc@example.com", password_hash="x", first_name="D", last_name="D")
    insert("users", id="u-none", email="none@example.com", password_hash="x", first_name="N", last_name="N")
    insert("roles", id=2, name="legacy-role")
    insert("user_roles", id="r1", user_id="u-single", role_id=2, organization_id="o-a")
    insert("user_roles", id="r2", user_id="u-multi", role_id=2, organization_id="o-a")
    insert("user_roles", id="r3", user_id="u-multi", role_id=2, organization_id="o-b")
    insert("doctor_profiles", id="dp1", user_id="u-doc", organization_id="o-b", clinic_name="c", specialty="s",
           license_number="l", status="APPROVED")
    legacy = {
        "a-single": dict(who_user_id="u-single", who_email="single@example.com"),
        "a-multi-with-details": dict(who_user_id="u-multi", who_email="multi@example.com", details=json.dumps({"organization_id": "o-b"})),
        "a-multi-no-details": dict(who_user_id="u-multi", who_email="multi@example.com"),
        "a-doctor": dict(who_user_id="u-doc", who_email="doc@example.com"),
        "a-email-only": dict(who_email="single@example.com"),
        "a-details-only": dict(who_email="ghost@example.com", details=json.dumps({"organization_id": "o-a"})),
        "a-unknown": dict(who_email="ghost@example.com"),
        "a-no-org-user": dict(who_user_id="u-none", who_email="none@example.com"),
    }
    for log_id, vals in legacy.items():
        insert("audit_logs", id=log_id, what_action="LEGACY", resource_type="X", result="SUCCESS", **vals)
    con.commit()
    con.close()

    alembic("upgrade", "head")
    con = sqlite3.connect(db_path)
    got = dict(con.execute("SELECT id, organization_id FROM audit_logs").fetchall())
    con.close()
    expected = {"a-single": "o-a", "a-multi-with-details": "o-b", "a-multi-no-details": None, "a-doctor": "o-b",
                "a-email-only": "o-a", "a-details-only": "o-a", "a-unknown": None, "a-no-org-user": None}
    assert got == expected, f"back-fill wrong:\nexpected {expected}\ngot      {got}"
    print("[PASS] Back-fill: single-org users, doctors, e-mail-only rows and event details are attributed; "
          "ambiguous, unknown and org-less rows stay NULL (system admin only).")

    print("\n========================================================")
    print("ALL ORGANIZATION-SCOPED AUDIT LOG TESTS PASSED SUCCESSFULLY")
    print("========================================================")


if __name__ == "__main__":
    run_tests()
