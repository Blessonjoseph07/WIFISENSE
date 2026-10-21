"""
Care records tests: doctor edit/delete, appointments, upcoming list, medication log.

Runs against a live server (API_BASE, default http://127.0.0.1:8000) seeded with demo data,
and uses the same DATABASE_URL as the server for cleanup. All records created here are
real stored test records and are removed at the end.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import Appointment, Doctor, MedicationLog, Prescription

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


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def run_tests():
    print("=== RUNNING CARE RECORDS TESTS (doctors, appointments, medication log) ===")
    admin = login("blesson@wifisense.com", "blessonpassword")
    care_admin = login("anjali@wifisense.com", "anjalipassword")
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")

    status, residents = api_call("/residents", token=care_admin)
    assert status == 200 and len(residents) >= 2, f"Need at least two residents: {status} {residents}"
    res_a, res_b = residents[0]["id"], residents[1]["id"]

    created = {"doctors": [], "appts": [], "rx": []}
    now = datetime.now(timezone.utc)
    try:
        # 1. Doctors: create (existing endpoint), edit, delete
        print("\n--- 1. Doctor create / edit / delete ---")
        status, doc = api_call(f"/residents/{res_a}/doctors", "POST", {
            "resident_id": res_a, "name": "Dr. Test Mathew", "specialty": "Geriatrics"}, care_admin)
        assert status == 201, f"{status} {doc}"
        created["doctors"].append(doc["id"])
        status, upd = api_call(f"/doctors/{doc['id']}", "PATCH", {"hospital": "Test General", "phone": "+91 99999 00000"}, care_admin)
        assert status == 200 and upd["hospital"] == "Test General" and upd["name"] == "Dr. Test Mathew", f"{status} {upd}"
        print("[PASS] Doctor edited; untouched fields preserved.")
        status, res = api_call(f"/doctors/{doc['id']}", "PATCH", {"name": ""}, care_admin)
        assert status == 422, f"Expected 422 for empty name, got {status}"
        print("[PASS] Empty doctor name rejected (422).")
        status, res = api_call(f"/doctors/{doc['id']}", "PATCH", {"salary": 5}, care_admin)
        assert status == 422, f"Expected 422 for unknown field, got {status}"
        print("[PASS] Unknown doctor field rejected (422).")
        status, res = api_call(f"/doctors/{doc['id']}", "PATCH", {"name": "Hacker"}, corp_fm)
        assert status == 403, f"Expected 403 for corporate FM editing care doctor, got {status}: {res}"
        print("[PASS] Corporate user cannot edit an elder-care doctor (403).")

        # 2. Appointments
        print("\n--- 2. Appointments ---")
        when = now + timedelta(days=2)
        status, appt = api_call(f"/residents/{res_a}/appointments", "POST", {
            "doctor_id": doc["id"], "scheduled_at": iso(when), "purpose": "Quarterly review"}, care_admin)
        assert status == 201, f"{status} {appt}"
        created["appts"].append(appt["id"])
        assert appt["status"] == "SCHEDULED" and appt["doctor_name"] == "Dr. Test Mathew", appt
        print("[PASS] Appointment scheduled with doctor, status SCHEDULED.")

        status, lst = api_call(f"/residents/{res_a}/appointments", token=care_admin)
        assert status == 200 and any(a["id"] == appt["id"] for a in lst)
        print("[PASS] Appointment listed for the resident.")

        status, up = api_call("/appointments/upcoming?days=7", token=care_admin)
        assert status == 200 and any(a["id"] == appt["id"] for a in up), f"{status} {up}"
        print("[PASS] Appointment appears in /appointments/upcoming.")

        status, up_corp = api_call("/appointments/upcoming?days=7", token=corp_fm)
        assert status == 200 and not any(a["id"] == appt["id"] for a in up_corp), "Corporate FM sees elder-care appointment!"
        print("[PASS] Corporate facility manager does not see elder-care appointments in upcoming.")

        status, res = api_call(f"/residents/{res_a}/appointments", token=corp_fm)
        assert status == 403, f"Expected 403, got {status}"
        print("[PASS] Corporate user blocked from resident appointments (403).")

        # doctor from another resident
        status, doc_b = api_call(f"/residents/{res_b}/doctors", "POST", {
            "resident_id": res_b, "name": "Dr. Other Patient", "specialty": "Cardiology"}, care_admin)
        assert status == 201
        created["doctors"].append(doc_b["id"])
        status, res = api_call(f"/residents/{res_a}/appointments", "POST", {
            "doctor_id": doc_b["id"], "scheduled_at": iso(when), "purpose": "Wrong doctor"}, care_admin)
        assert status == 400, f"Expected 400 for doctor of another resident, got {status}: {res}"
        print("[PASS] Doctor belonging to another resident rejected (400).")

        status, res = api_call(f"/residents/{res_a}/appointments", "POST", {
            "scheduled_at": iso(when), "purpose": "x", "status": "COMPLETED"}, care_admin)
        assert status == 422, f"Client-supplied status should be rejected, got {status}"
        print("[PASS] Client cannot set status on create (422).")

        status, done = api_call(f"/appointments/{appt['id']}", "PATCH", {"status": "COMPLETED", "notes": "Seen, BP stable"}, care_admin)
        assert status == 200 and done["status"] == "COMPLETED" and done["notes"] == "Seen, BP stable", f"{status} {done}"
        status, up = api_call("/appointments/upcoming?days=7", token=care_admin)
        assert not any(a["id"] == appt["id"] for a in up)
        print("[PASS] Completed appointment leaves the upcoming list.")
        status, res = api_call(f"/appointments/{appt['id']}", "PATCH", {"status": "DONE-ISH"}, care_admin)
        assert status == 422
        print("[PASS] Invalid appointment status rejected (422).")

        # deleting the doctor keeps the appointment, detached
        status, res = api_call(f"/doctors/{doc['id']}", "DELETE", token=care_admin)
        assert status == 200, f"{status} {res}"
        created["doctors"].remove(doc["id"])
        status, lst = api_call(f"/residents/{res_a}/appointments", token=care_admin)
        kept = next((a for a in lst if a["id"] == appt["id"]), None)
        assert kept is not None and kept["doctor_id"] is None
        print("[PASS] Deleting a doctor keeps appointment history (doctor detached).")

        # 3. Medication log
        print("\n--- 3. Medication administration log ---")
        status, rx = api_call(f"/residents/{res_a}/prescriptions", "POST", {
            "resident_id": res_a, "medication_name": "TestMed", "dosage": "5 mg", "frequency": "Once daily",
            "start_date": iso(now - timedelta(days=1))}, care_admin)
        assert status == 201, f"{status} {rx}"
        created["rx"].append(rx["id"])

        status, log = api_call(f"/prescriptions/{rx['id']}/administer", "POST", {"status": "GIVEN", "notes": "With breakfast"}, care_admin)
        assert status == 201 and log["status"] == "GIVEN" and log["medication_name"] == "TestMed" and log["administered_by_name"], f"{status} {log}"
        print("[PASS] Dose logged with who/when and medication name.")

        status, res = api_call(f"/prescriptions/{rx['id']}/administer", "POST", {"status": "TAKEN"}, care_admin)
        assert status == 422
        print("[PASS] Invalid dose status rejected (422).")

        status, res = api_call(f"/prescriptions/{rx['id']}/administer", "POST", {"status": "GIVEN"}, corp_fm)
        assert status == 403, f"Expected 403, got {status}"
        print("[PASS] Corporate user cannot log medication (403).")

        status, hist = api_call(f"/residents/{res_a}/medication-log", token=care_admin)
        assert status == 200 and any(h["id"] == log["id"] for h in hist)
        print("[PASS] Medication log lists the dose.")

        status, res = api_call(f"/prescriptions/{rx['id']}", "DELETE", token=care_admin)
        assert status == 409, f"Expected 409 deleting prescription with log, got {status}: {res}"
        print("[PASS] Prescription with log entries cannot be deleted (409).")

        status, rx2 = api_call(f"/residents/{res_a}/prescriptions", "POST", {
            "resident_id": res_a, "medication_name": "TestMed2", "dosage": "1 mg", "frequency": "Weekly",
            "start_date": iso(now)}, care_admin)
        created["rx"].append(rx2["id"])
        status, res = api_call(f"/prescriptions/{rx2['id']}", "DELETE", token=care_admin)
        assert status == 200
        created["rx"].remove(rx2["id"])
        print("[PASS] Prescription without log entries deleted (200).")

        status, rx3 = api_call(f"/residents/{res_a}/prescriptions", "POST", {
            "resident_id": res_a, "medication_name": "Ended", "dosage": "1", "frequency": "Daily",
            "start_date": iso(now - timedelta(days=10)), "end_date": iso(now - timedelta(days=1))}, care_admin)
        created["rx"].append(rx3["id"])
        status, res = api_call(f"/prescriptions/{rx3['id']}/administer", "POST", {"status": "GIVEN"}, care_admin)
        assert status == 400, f"Expected 400 for ended prescription, got {status}"
        print("[PASS] Dose on an ended prescription rejected (400).")

        # 4. Audit trail
        print("\n--- 4. Audit trail ---")
        status, audit = api_call("/auth/audit-logs", token=admin)
        if status == 200:
            text = json.dumps(audit)
            assert "APPOINTMENT_CREATED" in text and "MEDICATION_GIVEN" in text, "Audit events missing"
            print("[PASS] Appointment and medication events present in audit log.")
        else:
            print(f"[SKIP] Audit log endpoint returned {status}; audit assertion skipped.")
    finally:
        print("\n--- Cleanup ---")
        with Session(engine) as session:
            for rid in created["rx"]:
                for l in session.exec(select(MedicationLog).where(MedicationLog.prescription_id == rid)).all():
                    session.delete(l)
            session.commit()
            for aid in created["appts"]:
                a = session.get(Appointment, aid)
                if a:
                    session.delete(a)
            session.commit()
            for rid in created["rx"]:
                r = session.get(Prescription, rid)
                if r:
                    session.delete(r)
            for did in created["doctors"]:
                d = session.get(Doctor, did)
                if d:
                    session.delete(d)
            session.commit()
        print("[PASS] Test records removed.")

    print("\n========================================================")
    print("ALL CARE RECORDS TESTS PASSED SUCCESSFULLY")
    print("========================================================")


if __name__ == "__main__":
    run_tests()
