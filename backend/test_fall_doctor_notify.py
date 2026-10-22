"""
FALL -> DOCTOR NOTIFICATION TEST SUITE
======================================
Care staff can tell a resident's doctors about a fall alert. Approved, assigned doctors get a message in their portal;
contact-record doctors get an email only if it can really be sent, and the result says exactly what happened.
Corporate users and doctors cannot use it, and a doctor only ever sees their own messages.
"""
import json
import os
import urllib.error
import urllib.request

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def call(path, method="GET", data=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API_BASE + path, data=json.dumps(data).encode() if data is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def login(email, password):
    st, body = call("/auth/login", "POST", {"email": email, "password": password})
    assert st == 200, (email, body)
    return body["access_token"]


def run():
    care_fm = login("anjali@wifisense.com", "anjalipassword")
    caregiver = login("abhinanth@wifisense.com", "abhinanthpassword")
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")
    corp_staff = login("tomy@wifisense.com", "tomypassword")
    doctor = login("mathew.varghese@wifisense.com", "doctorpassword")  # approved, assigned to Mary and Annamma

    st, residents = call("/residents", token=care_fm)
    mary = next(r for r in residents if r["first_name"] == "Mary")
    st, alerts = call("/alerts", token=care_fm)
    alert = next((a for a in alerts if a["room_id"] == mary["room_id"] and a["event_type"] == "Fall_Detected"), None)
    other_room_alert = next((a for a in alerts if a["room_id"] != mary["room_id"]), None)
    path = f"/medical/residents/{mary['id']}/notify-doctors"

    print("--- who may notify")
    assert call(path, "POST", {}, corp_fm)[0] in (403, 404)
    assert call(path, "POST", {}, corp_staff)[0] in (403, 404)
    assert call(path, "POST", {}, doctor)[0] == 403
    assert call(path, "POST", {"surprise": 1}, care_fm)[0] == 422
    if other_room_alert:
        st, _ = call(path, "POST", {"alert_id": other_room_alert["id"]}, care_fm)
        assert st == 400, "an alert from another room must not be attached to this resident"
    print("[PASS] corporate users and doctors refused; unknown fields rejected; foreign alert refused")

    print("--- notify")
    body = {"alert_id": alert["id"]} if alert else {}
    body["note"] = "Please advise."
    st, res = call(path, "POST", body, caregiver)
    assert st == 200, (st, res)
    assert res["resident"] == "Mary Joseph" and "Fall alert: Mary Joseph" in res["message"] and "Please advise." in res["message"], res
    portal = [r for r in res["results"] if r["channel"] == "doctor portal"]
    assert any("Mathew" in r["doctor"] and r["status"].startswith("delivered") for r in portal), res["results"]
    for r in res["results"]:
        if r["channel"] == "email":
            assert r["status"].startswith("email sent") or "NOT sent" in r["status"], r      # never claims a send that did not happen
        if r["channel"] == "contact record":
            assert "call" in r["status"].lower() or "no email or phone" in r["status"], r
    print("[PASS] portal doctor delivered; every other doctor reported with its real outcome:",
          "; ".join(f"{r['doctor']}: {r['status']}" for r in res["results"]))

    if alert:
        st, again = call(path, "POST", {"alert_id": alert["id"]}, caregiver)
        assert st == 200 and any(r["status"].startswith("already informed") for r in again["results"] if r["channel"] == "doctor portal")
        print("[PASS] the same alert does not message the same doctor twice")

    print("--- doctor inbox")
    st, inbox = call("/medical/notifications", token=doctor)
    assert st == 200 and inbox and inbox[0]["resident_name"] == "Mary Joseph" and inbox[0]["read"] is False, inbox
    nid = inbox[0]["id"]
    st, done = call(f"/medical/notifications/{nid}/read", "POST", {}, doctor)
    assert st == 200 and done["read"] is True
    assert call("/medical/notifications/not-a-real-id/read", "POST", {}, doctor)[0] == 404
    assert call("/medical/notifications", token=care_fm)[0] == 403, "staff are not doctors"
    print("[PASS] the doctor sees the message, can mark it read; staff cannot read a doctor's inbox")


if __name__ == "__main__":
    print("=== FALL -> DOCTOR NOTIFICATION TESTS ===")
    run()
    print("\nALL FALL -> DOCTOR NOTIFICATION TESTS PASSED")
