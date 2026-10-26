"""
ROOM PICKER TEST
================
GET /rooms says where each room lives (organization name and type, building) so the device-registration dialog can group
its dropdown into Corporate and Elder Care, and organization admins still only see their own rooms.
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
    assert st == 200, body
    return body["access_token"]


def run():
    admin = login("blesson@wifisense.com", "blessonpassword")
    care = login("elizabeth@wifisense.com", "elizabethpassword")
    corp = login("abhinand@wifisense.com", "abhinandpassword")

    st, rooms = call("/rooms", token=admin)
    assert st == 200 and rooms
    assert all(r["organization_name"] and r["organization_type"] in ("CORPORATE", "ELDER_CARE") and r["building_name"] for r in rooms), \
        "every room must say which organization and building it belongs to"
    types = {r["organization_type"] for r in rooms}
    assert types == {"CORPORATE", "ELDER_CARE"}, types
    print(f"[PASS] system admin sees {len(rooms)} rooms, each labelled with organization, type and building")

    st, care_rooms = call("/rooms", token=care)
    assert st == 200 and {r["organization_type"] for r in care_rooms} == {"ELDER_CARE"}, "elder-care manager must only see elder-care rooms"
    st, corp_rooms = call("/rooms", token=corp)
    assert st == 200 and {r["organization_type"] for r in corp_rooms} == {"CORPORATE"}, "corporate manager must only see corporate rooms"
    assert not {r["id"] for r in care_rooms} & {r["id"] for r in corp_rooms}
    print("[PASS] organization managers still see only their own rooms")

    # GET /devices must say where each device is: the fields used to be dropped from the response, so the Devices page
    # showed the elder-care home for every device, corporate rooms included.
    st, devices = call("/devices", token=admin)
    assert st == 200 and devices
    room_org = {r["id"]: r["organization_type"] for r in rooms}
    placed = [d for d in devices if d.get("room_id") in room_org]
    assert placed and all(d.get("organization_type") == room_org[d["room_id"]] and d.get("organization_name") and d.get("room_name")
                          for d in placed), [(d["mac_address"], d.get("organization_type"), d.get("room_name")) for d in placed[:5]]
    assert {d["organization_type"] for d in placed} == {"CORPORATE", "ELDER_CARE"}
    print(f"[PASS] /devices labels all {len(placed)} placed devices with their own room's organization (corporate and elder care)")
    print("\nALL ROOM PICKER TESTS PASSED")


if __name__ == "__main__":
    run()
