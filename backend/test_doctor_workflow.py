"""
Medical provider workflow tests: apply -> organization approval -> explicit resident assignment -> doctor access.

Runs against a live seeded server (API_BASE, default http://127.0.0.1:8000) and uses the same DATABASE_URL for
setup/cleanup. Fall alerts here come from /sensing/simulate-event and are labelled simulated.
"""
import os
import json
import time
import urllib.request
import urllib.error
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import hash_password
from app.models.entities import (
    Alert, AlertAcknowledgement, Allergy, Building, Consultation, DoctorAssignment, DoctorProfile, Floor,
    HealthCondition, Organization, Prescription, RefreshToken, Resident, Room, SensingDevice, SensingEvent, User,
    UserRole,
)

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


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


def login(email, password):
    status, res = api_call("/auth/login", "POST", {"email": email, "password": password})
    assert status == 200, f"Login failed for {email}: {status} {res}"
    return res["access_token"]


def run_tests():
    print("=== RUNNING MEDICAL PROVIDER WORKFLOW TESTS ===")
    stamp = str(int(time.time()))
    new_email = f"newdoc{stamp}@example.com"
    new_pw = "NewDoctorPass#1"

    admin = login("blesson@wifisense.com", "blessonpassword")
    care_admin = login("anjali@wifisense.com", "anjalipassword")
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")
    mathew = login("mathew.varghese@wifisense.com", "doctorpassword")  # seeded, approved, assigned to Mary + Annamma

    with Session(engine) as session:
        care_org = session.exec(select(Organization).where(Organization.type == "ELDER_CARE")).first()
        corp_org = session.exec(select(Organization).where(Organization.type == "CORPORATE")).first()
        residents = {f"{r.first_name} {r.last_name}": r for r in session.exec(select(Resident)).all()}
        mary, annamma = residents["Mary Joseph"], residents["Annamma Joseph"]
        other = next(r for n, r in residents.items() if n not in ("Mary Joseph", "Annamma Joseph"))
        care_org_id, corp_org_id = care_org.id, corp_org.id
        mary_id, annamma_id, other_id = mary.id, annamma.id, other.id
        mary_room_id, other_room_id = mary.room_id, other.room_id
        dev_mary = session.exec(select(SensingDevice).where(SensingDevice.room_id == mary_room_id)).first()
        dev_mary_id = dev_mary.id if dev_mary else None

    cleanup = {"users": [], "profiles": [], "alerts": [], "events": [], "extra": {"conditions": [], "rx": []}, "org2": None}

    try:
        # ------------------------------------------------------------------ 1. apply
        print("\n--- 1. Doctor application ---")
        status, res = api_call("/auth/register", "POST", {
            "email": new_email, "password": new_pw, "first_name": "Dr. New", "last_name": "Applicant",
            "role": "system_admin"})
        assert status == 201, f"Registration must work (regression: it used to return 500): {status} {res}"
        cleanup["users"].append(res["id"])
        status, lg = api_call("/auth/login", "POST", {"email": new_email, "password": new_pw})
        assert status == 200 and lg["role"] == "family_member" and lg["is_system_admin"] is False, lg
        new_doc = lg["access_token"]
        print("[PASS] Registration works, and a client-supplied role is ignored: the account is a plain family_member.")

        status, res = api_call("/medical/my-residents", token=new_doc)
        assert status == 403, f"Plain user must not use doctor portal, got {status}"
        print("[PASS] Plain registered user denied doctor portal (403).")

        status, res = api_call("/medical/apply", "POST", {
            "organization_id": corp_org_id, "clinic_name": "Corp Clinic", "specialty": "GP", "license_number": "X-123"}, new_doc)
        assert status == 400, f"Corporate org must be refused, got {status}"
        status, res = api_call("/medical/apply", "POST", {
            "organization_id": care_org_id, "clinic_name": "Test Clinic", "specialty": "Neurology",
            "license_number": "TEST-9001", "role": "system_admin"}, new_doc)
        assert status == 422, f"Unknown field must be rejected, got {status}"
        status, res = api_call("/medical/apply", "POST", {
            "organization_id": care_org_id, "clinic_name": "Test Clinic", "specialty": "Neurology",
            "license_number": "TEST-9001"}, new_doc)
        assert status == 201 and res["status"] == "PENDING", f"{status} {res}"
        new_profile_id = res["id"]
        cleanup["profiles"].append(new_profile_id)
        print("[PASS] Application created as PENDING; corporate org and extra fields refused.")

        status, res = api_call("/medical/apply", "POST", {
            "organization_id": care_org_id, "clinic_name": "Again", "specialty": "GP", "license_number": "DUP-1"}, new_doc)
        assert status == 409
        print("[PASS] Second application refused (409).")

        status, res = api_call("/medical/my-residents", token=new_doc)
        assert status == 403
        print("[PASS] PENDING doctor still denied.")

        # ------------------------------------------------------------------ 2. org review
        print("\n--- 2. Organization review ---")
        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "APPROVE"}, corp_fm)
        assert status in (403, 404), f"Corporate staff must not review elder-care doctors, got {status}"
        print(f"[PASS] Corporate facility manager cannot review an elder-care doctor ({status}).")

        status, res = api_call("/medical/providers?status=PENDING", token=care_admin)
        assert status == 200 and any(p["id"] == new_profile_id for p in res), res
        print("[PASS] Organization admin sees pending applications.")

        status, res = api_call("/medical/providers", token=mathew)
        assert status == 403, f"Doctor must not list providers, got {status}"

        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "REJECT"}, care_admin)
        assert status == 422, f"Reject without note should be 422, got {status}"
        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "APPROVE"}, care_admin)
        assert status == 200 and res["status"] == "APPROVED", f"{status} {res}"
        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "APPROVE"}, care_admin)
        assert status == 409
        print("[PASS] Reject needs a note; approval works once; repeat approval refused (409).")

        new_doc = login(new_email, new_pw)  # role resolved again after approval
        status, res = api_call("/medical/my-residents", token=new_doc)
        assert status == 200 and res == [], f"Approved doctor with no assignments should see nothing: {status} {res}"
        print("[PASS] Approved doctor with no assignments sees no residents.")

        # ------------------------------------------------------------------ 3. default deny elsewhere
        print("\n--- 3. Doctors are denied everywhere else ---")
        for path in ("/residents", "/alerts", f"/residents/{mary_id}/profile-details", "/appointments/upcoming",
                     "/sensing/history", f"/residents/{mary_id}/doctors", "/organizations"):
            status, res = api_call(path, token=mathew)
            assert status in (401, 403), f"Doctor reached {path}: {status}"
        print("[PASS] Approved doctor is denied residents, alerts, profiles, appointments, history, org endpoints.")

        # ------------------------------------------------------------------ 4. assignments
        print("\n--- 4. Assignments ---")
        status, res = api_call("/medical/assignments", "POST", {"doctor_profile_id": new_profile_id, "resident_id": mary_id}, corp_fm)
        assert status in (403, 404), f"Corporate user assigned a doctor: {status}"
        status, res = api_call("/medical/assignments", "POST", {"doctor_profile_id": new_profile_id, "resident_id": mary_id}, mathew)
        assert status == 403
        print("[PASS] Corporate staff and doctors cannot create assignments.")

        status, pend = api_call("/medical/providers?status=PENDING", token=care_admin)
        priya = next(p for p in pend if p["email"] == "priya.nair@wifisense.com")
        status, res = api_call("/medical/assignments", "POST", {"doctor_profile_id": priya["id"], "resident_id": mary_id}, care_admin)
        assert status == 409, f"Pending doctor must not be assignable, got {status}"
        print("[PASS] Pending doctor cannot be assigned (409).")

        # second elder-care organization with its own resident
        with Session(engine) as session:
            org2 = Organization(name=f"Other Care Home {stamp}", type="ELDER_CARE")
            session.add(org2)
            session.commit()
            b2 = Building(organization_id=org2.id, name="B2")
            session.add(b2)
            session.commit()
            f2 = Floor(building_id=b2.id, floor_number=1)
            session.add(f2)
            session.commit()
            r2 = Room(floor_id=f2.id, name=f"Room X{stamp}", room_type="Bedroom")
            session.add(r2)
            session.commit()
            res2 = Resident(room_id=r2.id, first_name="Foreign", last_name="Resident")
            session.add(res2)
            session.commit()
            ou = User(email=f"orgdoc{stamp}@example.com", password_hash=hash_password("x"), first_name="Dr. Org", last_name="Two", is_active=True)
            session.add(ou)
            session.commit()
            dp2 = DoctorProfile(user_id=ou.id, organization_id=org2.id, clinic_name="Other", specialty="GP",
                                license_number="O2-1", status="PENDING")
            session.add(dp2)
            session.commit()
            cleanup["org2"] = dict(org=org2.id, bld=b2.id, floor=f2.id, room=r2.id, resident=res2.id, user=ou.id, profile=dp2.id)
            foreign_resident_id, foreign_profile_id = res2.id, dp2.id

        status, res = api_call("/medical/assignments", "POST", {"doctor_profile_id": new_profile_id, "resident_id": foreign_resident_id}, care_admin)
        assert status == 403, f"Cross-organization assignment must be refused, got {status}: {res}"
        print("[PASS] A doctor cannot be assigned to a resident of another organization (403).")

        status, res = api_call("/medical/providers", token=care_admin)
        assert not any(p["id"] == foreign_profile_id for p in res), "Org admin sees another organization's doctors!"
        status, res = api_call(f"/medical/providers/{foreign_profile_id}/review", "PATCH", {"decision": "APPROVE"}, care_admin)
        assert status == 404, f"Org admin reviewed another organization's doctor: {status}"
        print("[PASS] Organization admin cannot see or review another organization's doctors.")

        status, a1 = api_call("/medical/assignments", "POST", {"doctor_profile_id": new_profile_id, "resident_id": mary_id}, care_admin)
        assert status == 201 and a1["status"] == "ACTIVE", f"{status} {a1}"
        status, res = api_call("/medical/assignments", "POST", {"doctor_profile_id": new_profile_id, "resident_id": mary_id}, care_admin)
        assert status == 409
        print("[PASS] Assignment created; duplicate refused (409).")

        # ------------------------------------------------------------------ 5. doctor access
        print("\n--- 5. Doctor access limited to assigned residents ---")
        status, mine = api_call("/medical/my-residents", token=mathew)
        assert status == 200
        assert sorted(r["name"] for r in mine) == ["Annamma Joseph", "Mary Joseph"], mine
        print("[PASS] Seeded doctor sees exactly the two assigned residents.")

        status, rec = api_call(f"/medical/residents/{mary_id}/record", token=mathew)
        assert status == 200 and rec["resident"]["name"] == "Mary Joseph", f"{status}"
        assert any(a["allergen"] == "Penicillin" for a in rec["allergies"]), rec["allergies"]
        for key in ("conditions", "prescriptions", "consultations", "lab_reports", "hospital_visits", "recent_fall_alerts"):
            assert key in rec, key
        print("[PASS] Assigned resident's record returned with allergies, medications, consultations and more.")

        status, res = api_call(f"/medical/residents/{other_id}/record", token=mathew)
        assert status == 403, f"Unassigned resident record leaked: {status}"
        status, res = api_call(f"/medical/residents/{other_id}/consultations", "POST", {"reason": "Sneaky visit"}, mathew)
        assert status == 403
        status, res = api_call(f"/medical/residents/{other_id}/allergies", "POST", {"allergen": "Dust"}, mathew)
        assert status == 403
        print("[PASS] Unassigned resident: record read and all writes denied (403).")

        status, res = api_call(f"/medical/residents/{mary_id}/record", token=new_doc)
        assert status == 200, f"Newly assigned doctor should see Mary: {status}"
        status, res = api_call(f"/medical/residents/{annamma_id}/record", token=new_doc)
        assert status == 403
        print("[PASS] Newly approved doctor sees only the resident they were assigned.")

        # ------------------------------------------------------------------ 6. records
        print("\n--- 6. Writing medical records ---")
        status, c = api_call(f"/medical/residents/{mary_id}/consultations", "POST", {
            "reason": "BP review", "notes": "Stable, continue medication.", "follow_up_date": "2026-11-20T10:00:00Z"}, mathew)
        assert status == 201 and c["follow_up_done"] is False and c["doctor_name"], f"{status} {c}"
        status, res = api_call(f"/medical/residents/{mary_id}/consultations", "POST", {"reason": "x", "role": "admin"}, mathew)
        assert status == 422
        status, res = api_call(f"/medical/consultations/{c['id']}/follow-up", "PATCH", {"done": True}, mathew)
        assert status == 200 and res["follow_up_done"] is True
        status, res = api_call(f"/medical/consultations/{c['id']}/follow-up", "PATCH", {"done": True}, new_doc)
        assert status == 200, "Another doctor assigned to the same resident may update follow-up"
        print("[PASS] Consultation with doctor notes and follow-up recorded and updated.")

        status, a = api_call(f"/medical/residents/{mary_id}/allergies", "POST", {"allergen": "Latex", "severity": "SEVERE", "reaction": "Anaphylaxis"}, mathew)
        assert status == 201
        status, res = api_call(f"/medical/residents/{mary_id}/allergies", "POST", {"allergen": "Dust", "severity": "EXTREME"}, mathew)
        assert status == 422
        status, cond = api_call(f"/medical/residents/{mary_id}/conditions", "POST", {"condition_name": "Hypertension", "notes": "Stage 1"}, mathew)
        assert status == 201
        cleanup["extra"]["conditions"].append(cond["id"])
        status, rx = api_call(f"/medical/residents/{mary_id}/prescriptions", "POST", {"medication_name": "Amlodipine", "dosage": "5 mg", "frequency": "Once daily"}, mathew)
        assert status == 201 and "Mathew" in rx["prescribed_by"], rx
        cleanup["extra"]["rx"].append(rx["id"])
        print("[PASS] Allergy (validated severity), condition and prescription recorded; prescriber taken from the login.")

        status, summ = api_call(f"/medical/residents/{mary_id}/staff-summary", token=care_admin)
        assert status == 200
        assert any(x["allergen"] == "Latex" for x in summ["allergies"]), summ
        assert all(not f["follow_up_done"] for f in summ["open_follow_ups"])
        status, res = api_call(f"/medical/residents/{mary_id}/staff-summary", token=corp_fm)
        assert status in (403, 404), f"Corporate user read elder-care medical summary: {status}"
        status, res = api_call(f"/medical/residents/{mary_id}/staff-summary", token=mathew)
        assert status == 403, "Doctors use the record endpoint, not the staff summary"
        print("[PASS] Care staff see allergies/consultations/follow-ups; corporate staff are denied.")

        # ------------------------------------------------------------------ 7. falls reach the medical workflow
        print("\n--- 7. Fall alerts reach assigned doctors only ---")
        assert dev_mary_id, "No device in Mary's room"
        status, res = api_call("/sensing/simulate-event", "POST", {
            "device_id": dev_mary_id, "simulated_activity": "Fall_Detected", "confidence": 0.5, "signal_quality": 90}, care_admin)
        assert status == 201, f"{status} {res}"
        cleanup["alerts"].append(res["alert"]["id"])
        cleanup["events"].append(res["sensing_event"]["id"])
        mary_alert = res["alert"]["id"]
        status, al = api_call("/medical/my-alerts", token=mathew)
        assert status == 200
        hit = next((a for a in al if a["alert_id"] == mary_alert), None)
        assert hit and hit["resident_name"] == "Mary Joseph" and hit["source"] == "simulated", al
        assert hit["confidence_level"] == "LOW" and hit["requires_verification"] is True, hit
        status, al_new = api_call("/medical/my-alerts", token=new_doc)
        assert any(a["alert_id"] == mary_alert for a in al_new)
        assert all(a["resident_name"] == "Mary Joseph" for a in al_new), "Doctor sees alerts of unassigned residents"
        print("[PASS] Fall alert (simulated, LOW confidence, verification required) visible to assigned doctors only.")

        status, rec = api_call(f"/medical/residents/{mary_id}/record", token=mathew)
        assert any(a["alert_id"] == mary_alert for a in rec["recent_fall_alerts"])
        print("[PASS] Resident record lists recent fall alerts with confidence and verification state.")

        # ------------------------------------------------------------------ 8. revoke / suspend are immediate
        print("\n--- 8. Revocation and suspension take effect immediately ---")
        status, res = api_call(f"/medical/assignments/{a1['id']}", "DELETE", token=corp_fm)
        assert status in (403, 404)
        status, res = api_call(f"/medical/assignments/{a1['id']}", "DELETE", token=care_admin)
        assert status == 200 and res["status"] == "REVOKED"
        status, res = api_call(f"/medical/residents/{mary_id}/record", token=new_doc)
        assert status == 403, "Revoked doctor still reads the record"
        status, res = api_call(f"/medical/assignments/{a1['id']}", "DELETE", token=care_admin)
        assert status == 409
        print("[PASS] Revoked assignment blocks access at once; double revoke refused (409).")

        status, a2 = api_call("/medical/assignments", "POST", {"doctor_profile_id": new_profile_id, "resident_id": mary_id}, care_admin)
        assert status == 201
        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "SUSPEND"}, care_admin)
        assert status == 422
        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "SUSPEND", "note": "License check pending"}, care_admin)
        assert status == 200 and res["status"] == "SUSPENDED"
        status, res = api_call(f"/medical/residents/{mary_id}/record", token=new_doc)
        assert status == 403, "Suspended doctor still reads the record"
        status, res = api_call(f"/medical/providers/{new_profile_id}/review", "PATCH", {"decision": "APPROVE"}, care_admin)
        assert status == 200 and res["status"] == "APPROVED"
        status, res = api_call(f"/medical/residents/{mary_id}/record", token=new_doc)
        assert status == 200
        print("[PASS] Suspension blocks the doctor immediately; reinstating restores the existing assignment.")

        # ------------------------------------------------------------------ 9. audit
        print("\n--- 9. Audit trail ---")
        for action in ("MEDICAL_RECORD_VIEWED", "MEDICAL_ACCESS_DENIED", "DOCTOR_APPROVE", "DOCTOR_ASSIGNED",
                       "DOCTOR_ASSIGNMENT_REVOKED", "CONSULTATION_RECORDED", "DOCTOR_SUSPEND"):
            status, logs = api_call(f"/auth/audit-logs?action={action}&limit=5", token=admin)
            assert status == 200 and len(logs) > 0, f"No audit entries for {action}"
        print("[PASS] Views, denials, approvals, assignments, revocations, suspensions and writes are all audited.")
    finally:
        print("\n--- Cleanup ---")
        with Session(engine) as session:
            for aid in cleanup["alerts"]:
                for ack in session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == aid)).all():
                    session.delete(ack)
                a = session.get(Alert, aid)
                if a:
                    session.delete(a)
            for eid in cleanup["events"]:
                e = session.get(SensingEvent, eid)
                if e:
                    session.delete(e)
            session.commit()
            profile_ids = list(cleanup["profiles"])
            org2 = cleanup["org2"]
            if org2:
                profile_ids.append(org2["profile"])
            for pid in profile_ids:
                for row in session.exec(select(Consultation).where(Consultation.doctor_profile_id == pid)).all():
                    session.delete(row)
                for row in session.exec(select(DoctorAssignment).where(DoctorAssignment.doctor_profile_id == pid)).all():
                    session.delete(row)
            session.commit()
            for cid in cleanup["extra"]["conditions"]:
                row = session.get(HealthCondition, cid)
                if row:
                    session.delete(row)
            for rid in cleanup["extra"]["rx"]:
                row = session.get(Prescription, rid)
                if row:
                    session.delete(row)
            for row in session.exec(select(Allergy).where(Allergy.allergen.in_(["Latex", "Dust"]))).all():
                session.delete(row)
            session.commit()
            for pid in profile_ids:
                row = session.get(DoctorProfile, pid)
                if row:
                    session.delete(row)
            session.commit()
            user_ids = list(cleanup["users"]) + ([org2["user"]] if org2 else [])
            for uid in user_ids:
                for row in session.exec(select(UserRole).where(UserRole.user_id == uid)).all():
                    session.delete(row)
                for row in session.exec(select(RefreshToken).where(RefreshToken.user_id == uid)).all():
                    session.delete(row)
            session.commit()
            for uid in user_ids:
                row = session.get(User, uid)
                if row:
                    session.delete(row)
            if org2:
                for model, key in ((Resident, "resident"), (Room, "room"), (Floor, "floor"), (Building, "bld"), (Organization, "org")):
                    row = session.get(model, org2[key])
                    if row:
                        session.delete(row)
            session.commit()
        print("[PASS] Test users, organization, records and alerts removed.")

    print("\n========================================================")
    print("ALL MEDICAL PROVIDER WORKFLOW TESTS PASSED SUCCESSFULLY")
    print("========================================================")


if __name__ == "__main__":
    run_tests()
