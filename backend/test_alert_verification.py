"""
Detection confidence, reliability and alert verification tests.

Runs against a live seeded server (API_BASE, default http://127.0.0.1:8000) and uses the same
DATABASE_URL for cleanup. Every event here is created through /sensing/simulate-event and is
therefore labelled source="simulated" - nothing in this file claims live capture.
"""
import os
import json
import urllib.request
import urllib.error
from sqlmodel import Session, select
from app.core.database import engine
from app.models.entities import (
    Alert, AlertAcknowledgement, Building, Floor, Organization, Room, SensingDevice, SensingEvent,
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
    print("=== RUNNING DETECTION CONFIDENCE & ALERT VERIFICATION TESTS (all events simulated) ===")
    care_admin = login("anjali@wifisense.com", "anjalipassword")
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")

    with Session(engine) as session:
        dev = session.exec(
            select(SensingDevice).join(Room).join(Floor).join(Building).join(Organization)
            .where(Organization.type == "ELDER_CARE")
        ).first()
        assert dev is not None, "No elder-care device found."
        device_id, device_mac = dev.id, dev.mac_address

    created_alerts, created_events = [], []

    def simulate(**extra):
        status, res = api_call("/sensing/simulate-event", "POST",
                               dict(device_id=device_id, simulated_activity="Fall_Detected", **extra), care_admin)
        assert status == 201, f"{status} {res}"
        created_events.append(res["sensing_event"]["id"])
        if res.get("alert"):
            created_alerts.append(res["alert"]["id"])
        return res

    try:
        print("\n--- 1. Confidence / signal levels and 'Verification Required' ---")
        res = simulate()
        ev = res["sensing_event"]
        assert ev["confidence_level"] == "HIGH" and ev["signal_level"] == "GOOD", ev
        assert ev["requires_verification"] is False and ev["source"] == "simulated", ev
        print("[PASS] Default simulated fall: HIGH confidence, GOOD signal, source=simulated, no verification needed.")
        high_alert = res["alert"]["id"]

        res = simulate(confidence=0.40, signal_quality=80)
        assert res["sensing_event"]["confidence_level"] == "LOW" and res["sensing_event"]["requires_verification"] is True
        low_alert = res["alert"]["id"]
        print("[PASS] Confidence 0.40 -> LOW and Verification Required.")

        res = simulate(confidence=0.95, signal_quality=30)
        assert res["sensing_event"]["signal_level"] == "POOR" and res["sensing_event"]["requires_verification"] is True
        poor_alert = res["alert"]["id"]
        print("[PASS] High confidence but signal quality 30 -> POOR signal and Verification Required.")

        res = simulate(confidence=0.70, signal_quality=80)
        assert res["sensing_event"]["confidence_level"] == "MEDIUM" and res["sensing_event"]["requires_verification"] is False
        print("[PASS] Confidence 0.70 -> MEDIUM, signal GOOD, no verification needed.")

        status, res = api_call("/sensing/simulate-event", "POST",
                               {"device_id": device_id, "simulated_activity": "Fall_Detected", "confidence": 1.5}, care_admin)
        assert status == 422, f"Expected 422 for confidence 1.5, got {status}"
        print("[PASS] Out-of-range confidence rejected (422).")

        print("\n--- 2. Alert detail carries evidence, device and source ---")
        status, detail = api_call(f"/alerts/{low_alert}", token=care_admin)
        assert status == 200, detail
        assert detail["confidence"] == 0.40 and detail["confidence_level"] == "LOW", detail
        assert detail["signal_quality"] == 80 and detail["signal_level"] == "GOOD", detail
        assert detail["device_mac"] == device_mac and detail["source"] == "simulated", detail
        assert detail["requires_verification"] is True and detail["verification_status"] == "UNVERIFIED", detail
        assert detail["message"].endswith("[SIMULATED]"), detail["message"]
        assert detail["resident_name"], "Alert should name the resident for an elder-care room"
        print("[PASS] Alert shows resident, device MAC, confidence, signal quality, source, and [SIMULATED] message.")

        print("\n--- 3. Verification workflow ---")
        status, res = api_call(f"/alerts/{low_alert}/verify", "PATCH", {"outcome": "DISMISSED"}, care_admin)
        assert status == 422, f"Dismiss without note should be 422, got {status}"
        print("[PASS] Dismissing without a note rejected (422).")

        status, res = api_call(f"/alerts/{low_alert}/verify", "PATCH", {"outcome": "MAYBE", "note": "x"}, care_admin)
        assert status == 422
        status, res = api_call(f"/alerts/{low_alert}/verify", "PATCH", {"outcome": "CONFIRMED", "extra": 1}, care_admin)
        assert status == 422
        print("[PASS] Invalid outcome / unknown field rejected (422).")

        status, res = api_call(f"/alerts/{low_alert}/verify", "PATCH", {"outcome": "CONFIRMED", "note": "Found resident on floor"}, corp_fm)
        assert status in (403, 404), f"Corporate user must not verify elder-care alert, got {status}"
        print(f"[PASS] Corporate user cannot verify an elder-care alert ({status}).")

        status, res = api_call(f"/alerts/{low_alert}/verify", "PATCH", {"outcome": "CONFIRMED", "note": "Found resident on floor"}, care_admin)
        assert status == 200, f"{status} {res}"
        assert res["verification_status"] == "CONFIRMED" and res["verified_by_name"] and res["verified_at"], res
        assert res["requires_verification"] is False and res["status"] != "resolved", res
        print("[PASS] Confirmed: recorded who/when/note; alert stays open for the care workflow.")

        status, res = api_call(f"/alerts/{low_alert}/verify", "PATCH", {"outcome": "DISMISSED", "note": "changed mind"}, care_admin)
        assert status == 409, f"Second verification should be 409, got {status}"
        print("[PASS] An alert cannot be verified twice (409).")

        status, res = api_call(f"/alerts/{poor_alert}/verify", "PATCH", {"outcome": "DISMISSED", "note": "Resident sat down, signal noisy"}, care_admin)
        assert status == 200 and res["verification_status"] == "DISMISSED" and res["status"] == "resolved", res
        assert "Dismissed as false alarm" in (res["acknowledgement"]["resolution_notes"] or ""), res["acknowledgement"]
        print("[PASS] Dismissed: alert resolved as false alarm with the reason kept.")

        print("\n--- 4. Emergency view shows real evidence, no invented values ---")
        # high_alert is still active and was created before medium; make the newest active fall a known LOW one
        res = simulate(confidence=0.45, signal_quality=60)
        newest = res["alert"]["id"]
        status, em = api_call("/alerts/emergency-active", token=care_admin)
        assert status == 200 and em["has_emergency"] is True, em
        assert em["alert_id"] == newest, "Expected the newest active fall alert"
        assert em["telemetry"]["confidence"] == 45.0 and em["telemetry"]["confidence_level"] == "LOW", em["telemetry"]
        assert em["telemetry"]["signal_quality"] == 60 and em["source"] == "simulated", em
        assert em["requires_verification"] is True
        print("[PASS] Emergency view reports the alert's own confidence/signal values and flags verification.")

        print("\n--- 5. Alerts without sensing evidence are not presented as confident ---")
        status, alerts = api_call("/alerts", token=care_admin)
        assert status == 200
        no_evidence = [a for a in alerts if a["confidence"] is None and a["verification_status"] == "UNVERIFIED"]
        assert no_evidence, "Expected seeded alerts without evidence"
        assert all(a["confidence_level"] == "UNKNOWN" and a["requires_verification"] for a in no_evidence)
        print(f"[PASS] {len(no_evidence)} alert(s) with no sensing evidence are UNKNOWN and require verification.")

        print("\n--- 6. Detection history and isolation ---")
        status, hist = api_call("/sensing/history?limit=20", token=care_admin)
        assert status == 200 and len(hist) > 0
        first = hist[0]
        for key in ("activity", "confidence", "confidence_level", "signal_quality", "signal_level", "source", "requires_verification", "room_name"):
            assert key in first, f"history missing {key}"
        assert first["source"] == "simulated"
        print("[PASS] Detection history returns activity, confidence, signal, source and room.")

        care_room_id = res["sensing_event"]["room_id"]
        status, corp_hist = api_call("/sensing/history?limit=200", token=corp_fm)
        assert status == 200
        assert not any(h["room_id"] == care_room_id for h in corp_hist), "Corporate user sees elder-care detections!"
        status, filtered = api_call(f"/sensing/history?room_id={care_room_id}&limit=5", token=care_admin)
        assert status == 200 and all(h["room_id"] == care_room_id for h in filtered)
        print("[PASS] Corporate user's history excludes elder-care rooms; room filter works.")

        status, res = api_call("/sensing/history?limit=500", token=care_admin)
        assert status == 422
        print("[PASS] History limit above 200 rejected (422).")
    finally:
        print("\n--- Cleanup ---")
        with Session(engine) as session:
            for aid in created_alerts:
                for ack in session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == aid)).all():
                    session.delete(ack)
                a = session.get(Alert, aid)
                if a:
                    session.delete(a)
            for eid in created_events:
                e = session.get(SensingEvent, eid)
                if e:
                    session.delete(e)
            session.commit()
        print("[PASS] Test alerts and events removed.")

    print("\n========================================================")
    print("ALL CONFIDENCE & VERIFICATION TESTS PASSED SUCCESSFULLY")
    print("========================================================")


if __name__ == "__main__":
    run_tests()
