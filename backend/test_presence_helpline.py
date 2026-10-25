"""
PRESENCE, HELPLINE AND PAYMENT-TEST ACCOUNT
===========================================
  * payer@wifisense.com exists, is approved for a resident and has NO plan, so the payment flow can be tried end to end
  * the care home helpline: a manager can set it for their own organization only, bad numbers are refused, families see it,
    and clearing it shows no number (nothing is invented)
  * possible-fall alerts that an earlier version raised from live hardware are closed automatically (live fall detection is off),
    while alerts from other sources are left alone
Runs against API_BASE (a seeded server) and DATABASE_URL.
"""
import json
import os
import urllib.error
import urllib.request
import uuid

from sqlmodel import Session, select

from app.core.database import engine
from app.models.entities import Alert, AlertAcknowledgement, FamilySubscription, Organization, Room, User

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
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    corp = login("abhinand@wifisense.com", "abhinandpassword")
    care = login("mary@wifisense.com", "marypassword")
    john = login("john@wifisense.com", "johnpassword")
    payer = login(os.getenv("PAYER_EMAIL", "payer@wifisense.com"), os.getenv("PAYER_PASSWORD", "payerpassword"))

    with Session(engine) as s:
        home = s.exec(select(Organization).where(Organization.type == "ELDER_CARE")).first()
        home_id, original_phone = home.id, home.contact_phone
        payer_id = s.exec(select(User).where(User.email == "payer@wifisense.com")).first().id

    try:
        print("--- the payment test account")
        st, sub = call("/payments/subscription", token=payer)
        assert st == 200 and sub["connection_approved"] is True and sub["subscription"] is None, sub
        assert sub["subscription"] is None and call("/family/resident-status", token=payer)[1]["linked"] is True
        st, co = call("/payments/checkout", "POST", token=payer)
        assert st == 201 and co["checkout"]["id"], (st, co)
        st, done = call(f"/payments/sandbox/checkout/{co['checkout']['id']}/complete", "POST", {"outcome": "success"}, payer)
        assert st == 200 and done["subscription"]["status"] == "ACTIVE", (st, done)
        print("[PASS] payer@: approved connection, no plan at first, a checkout makes it ACTIVE")

        print("--- the helpline")
        st, org = call(f"/organizations/{home_id}/contact", "PATCH", {"contact_phone": "+91 481 2000 123"}, fm)
        assert st == 200 and org["contact_phone"] == "+91 481 2000 123", (st, org)
        st, fs = call("/family/resident-status", token=john)
        assert fs["facility_phone"] == "+91 481 2000 123" and fs["facility_name"], fs
        assert call(f"/organizations/{home_id}/contact", "PATCH", {"contact_phone": "+91 481 2000 123"}, corp)[0] == 404, "another organization's manager must not edit it"
        assert call(f"/organizations/{home_id}/contact", "PATCH", {"contact_phone": "+91 481 2000 123"}, care)[0] == 403, "a caregiver must not edit it"
        for bad in ("call me!", "<script>", "12", "1" * 40, "+91 00000 1234666660000", "+91 00000 00000", "+91 98470", "98+470 12345"):
            assert call(f"/organizations/{home_id}/contact", "PATCH", {"contact_phone": bad}, fm)[0] == 422, bad
        for good in ("+91 98470 12345", "0481 2000123", "1800 425 1234", "+44 20 7946 0958"):
            st, org = call(f"/organizations/{home_id}/contact", "PATCH", {"contact_phone": good}, fm)
            assert st == 200 and org["contact_phone"] == good, (good, st, org)
        print("[PASS] helpline numbers: wrong digit counts, repeated digits and a misplaced + are refused; real formats accepted")
        st, org = call(f"/organizations/{home_id}/contact", "PATCH", {"contact_phone": ""}, fm)
        assert st == 200 and org["contact_phone"] is None
        assert call("/family/resident-status", token=john)[1]["facility_phone"] is None, "nothing may be invented when no helpline is set"
        print("[PASS] set by its own manager (families see it), others refused (404/403), bad numbers 422, cleared = no number shown")

        print("--- stale live fall alerts are closed, other alerts are not")
        with Session(engine) as s:
            room = s.exec(select(Room)).first()
            live = Alert(room_id=room.id, event_type="Fall_Detected", severity="CRITICAL", status="new", source="live",
                         message="Possible fall in " + room.name + " [LIVE HARDWARE] - verification required")
            demo = Alert(room_id=room.id, event_type="Fall_Detected", severity="CRITICAL", status="new", source="simulated",
                         message="Possible fall in " + room.name + " [demo] " + uuid.uuid4().hex[:6])
            s.add(live)
            s.add(demo)
            s.commit()
            live_id, demo_id = live.id, demo.id
            from app.services.detection import close_stale_live_fall_alerts
            assert close_stale_live_fall_alerts(s) >= 1
            s.expire_all()
            assert s.get(Alert, live_id).status == "resolved" and s.get(Alert, live_id).verification_status == "DISMISSED"
            ack = s.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == live_id)).first()
            assert ack and "fall model was never validated" in ack.resolution_notes
            assert s.get(Alert, demo_id).status == "new", "alerts from other sources must be left alone"
            for aid in (live_id, demo_id):
                for a in s.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == aid)).all():
                    s.delete(a)
                s.delete(s.get(Alert, aid))
            s.commit()
        print("[PASS] a live 'Possible fall' alert is auto-resolved with a note; a non-live one stays open")
        print("\nALL PRESENCE / HELPLINE TESTS PASSED")
    finally:
        with Session(engine) as s:
            org = s.get(Organization, home_id)
            org.contact_phone = original_phone
            s.add(org)
            for row in s.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == payer_id)).all():
                s.delete(row)               # leave the payment test account without a plan, ready for the next try
            s.commit()


if __name__ == "__main__":
    run()
