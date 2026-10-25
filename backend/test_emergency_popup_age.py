"""
EMERGENCY POP-UP ONLY FOR RECENT FALLS
======================================
  * an open fall alert older than EMERGENCY_POPUP_MAX_AGE_MINUTES never takes over the caregiver's screen at login
  * a fresh open fall still does
Runs against API_BASE (a seeded server) and DATABASE_URL.
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.models.entities import Alert, Room

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


def add_fall(room_id, age):
    with Session(engine) as s:
        a = Alert(room_id=room_id, event_type="Fall_Detected", severity="CRITICAL", status="new",
                  message="TEST emergency pop-up age", created_at=datetime.now(timezone.utc) - age)
        s.add(a)
        s.commit()
        return a.id


def run_tests():
    print("=== EMERGENCY POP-UP AGE TESTS ===")
    token = login("mary@wifisense.com", "marypassword")
    with Session(engine) as s:
        room = s.exec(select(Room).where(Room.name == "Resident Room 204")).first()
    assert room, "Expected the seeded Resident Room 204"
    created = []
    try:
        old_id = add_fall(room.id, timedelta(minutes=settings.EMERGENCY_POPUP_MAX_AGE_MINUTES + 60))
        created.append(old_id)
        st, em = call("/alerts/emergency-active", token=token)
        assert st == 200, em
        assert em.get("alert_id") != old_id, "A stale open fall must not pop up"
        print("[PASS] An open fall older than the pop-up window does not take over the screen.")

        new_id = add_fall(room.id, timedelta(seconds=1))
        created.append(new_id)
        st, em = call("/alerts/emergency-active", token=token)
        assert st == 200 and em["has_emergency"] is True and em["alert_id"] == new_id, em
        print("[PASS] A fresh open fall still pops up.")

        st, alerts = call("/alerts", token=token)
        assert st == 200 and any(a["id"] == old_id for a in alerts), "The stale fall must still be listed"
        print("[PASS] The stale fall is still in the alert list.")
    finally:
        with Session(engine) as s:
            for aid in created:
                a = s.get(Alert, aid)
                if a:
                    s.delete(a)
            s.commit()
        print("Cleaned up test alerts.")
    print("ALL EMERGENCY POP-UP AGE TESTS PASSED")


if __name__ == "__main__":
    run_tests()
