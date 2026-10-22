"""
ROOM BOOKING TEST SUITE (corporate rooms)
=========================================
Facility managers book and cancel rooms; corporate staff see bookings and get the five-minute vacate reminder;
elder-care users never see corporate bookings; conflicts, past times and bad ranges are rejected.
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

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
    assert st == 200, body
    return body["access_token"]


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def run():
    fm = login("abhinand@wifisense.com", "abhinandpassword")        # corporate facility manager
    staff = login("tomy@wifisense.com", "tomypassword")             # corporate staff
    care_fm = login("elizabeth@wifisense.com", "elizabethpassword")  # elder-care facility manager

    st, rooms = call("/rooms", token=fm)
    assert st == 200 and len(rooms) >= 2, rooms
    room_a, room_b = rooms[0], rooms[1]
    care_rooms = call("/rooms", token=care_fm)[1]
    assert care_rooms and not {r["id"] for r in care_rooms} & {r["id"] for r in rooms}, "corporate and care rooms must be disjoint"

    now = datetime.now(timezone.utc)
    far = now + timedelta(days=30, hours=int.from_bytes(os.urandom(1), "big") % 20)
    created = []

    def book(token, room, start, end, purpose="Test seminar"):
        return call("/bookings", "POST", {"room_id": room["id"], "purpose": purpose, "start_at": iso(start), "end_at": iso(end)}, token)

    print("--- who may book")
    st, _ = book(staff, room_a, far, far + timedelta(hours=1))
    assert st == 403, st
    st, _ = book(care_fm, room_a, far, far + timedelta(hours=1))
    assert st == 404, st
    st, _ = book(care_fm, care_rooms[0], far, far + timedelta(hours=1))
    assert st in (400, 404), st
    print("[PASS] staff 403; elder-care manager cannot book corporate rooms; corporate rooms only")

    print("--- validation")
    assert book(fm, room_a, far + timedelta(hours=2), far + timedelta(hours=1))[0] == 400
    assert book(fm, room_a, far, far + timedelta(hours=13))[0] == 400
    assert book(fm, room_a, now - timedelta(hours=3), now - timedelta(hours=2))[0] == 400
    assert call("/bookings", "POST", {"room_id": room_a["id"], "purpose": "x", "start_at": iso(far), "end_at": iso(far + timedelta(hours=1))}, fm)[0] == 422
    print("[PASS] end<=start, >12h, past start, too-short purpose rejected")

    print("--- create, conflict, adjacent")
    st, b1 = book(fm, room_a, far, far + timedelta(hours=1), "Budget review")
    assert st == 201 and b1["status"] == "BOOKED" and b1["room_name"] == room_a["name"], b1
    created.append(b1["id"])
    st, body = book(fm, room_a, far + timedelta(minutes=30), far + timedelta(hours=2))
    assert st == 409 and "already booked" in body["detail"], body
    st, b2 = book(fm, room_a, far + timedelta(hours=1), far + timedelta(hours=2), "Back to back")
    assert st == 201, b2
    created.append(b2["id"])
    print("[PASS] overlap -> 409, back-to-back allowed")

    print("--- visibility")
    st, rows = call("/bookings", token=staff)
    assert st == 200 and b1["id"] in {r["id"] for r in rows}
    st, rows = call("/bookings", token=care_fm)
    assert st == 403 or b1["id"] not in {r["id"] for r in rows}, "elder-care user must not see corporate bookings"
    print("[PASS] staff can read; elder-care user cannot see them")

    print("--- five-minute vacate reminder")
    soon = now + timedelta(minutes=3)
    st, b3 = book(fm, room_b, soon, soon + timedelta(minutes=45), "Thesis defence")
    assert st == 201, b3
    created.append(b3["id"])
    st, rem = call("/bookings/reminders", token=staff)
    mine = [r for r in rem if r["booking_id"] == b3["id"]]
    assert st == 200 and len(mine) == 1, rem
    assert 1 <= mine[0]["minutes_until_start"] <= 4 and "vacate" in mine[0]["message"].lower() and "Thesis defence" in mine[0]["message"], mine[0]
    assert b1["id"] not in {r["booking_id"] for r in rem}, "a booking 30 days away must not trigger a reminder"
    st, rem2 = call("/bookings/reminders", token=care_fm)
    assert st == 403 or not [r for r in rem2 if r["booking_id"] == b3["id"]]
    print(f"[PASS] reminder: {mine[0]['message']}")

    print("--- cancel")
    st, _ = call(f"/bookings/{b3['id']}/cancel", "POST", {"reason": "meeting called off"}, staff)
    assert st == 403, st
    st, _ = call(f"/bookings/{b3['id']}/cancel", "POST", {"reason": "x"}, care_fm)
    assert st in (403, 404), st
    st, done = call(f"/bookings/{b3['id']}/cancel", "POST", {"reason": "meeting called off"}, fm)
    assert st == 200 and done["status"] == "CANCELLED" and done["cancel_reason"] == "meeting called off", done
    assert call(f"/bookings/{b3['id']}/cancel", "POST", {}, fm)[0] == 409
    rem = call("/bookings/reminders", token=staff)[1]
    assert b3["id"] not in {r["booking_id"] for r in rem}, "a cancelled booking must not remind anyone"
    st, again = book(fm, room_b, soon, soon + timedelta(minutes=45), "Rebooked")
    assert st == 201, again
    created.append(again["id"])
    print("[PASS] staff cannot cancel; manager can; no reminder after cancel; slot is free again")

    for bid in created:
        call(f"/bookings/{bid}/cancel", "POST", {}, fm)


if __name__ == "__main__":
    print("=== ROOM BOOKING TESTS ===")
    run()
    print("\nALL ROOM BOOKING TESTS PASSED")
