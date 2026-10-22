"""
LIVE CSI STREAM ENDPOINT TEST SUITE
===================================
GET /sensing/devices/{id}/live returns what a device really sent, with derived link physics.
Checks: provenance mode, wavelength derived from the channel, per-subcarrier amplitude/phase, incremental polling,
silent device returns nothing, no position fields, and that another organization gets 404.
"""
import json
import os
import urllib.error
import urllib.request

import numpy as np

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def call(path, method="GET", data=None, token=None, headers=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    h.update(headers or {})
    req = urllib.request.Request(API_BASE + path, data=json.dumps(data).encode() if data is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def login(email, password):
    status, body = call("/auth/login", "POST", {"email": email, "password": password})
    assert status == 200, body
    return body["access_token"]


def packet(seq, rng):
    iq = [int(v) for v in np.clip(np.round(rng.normal(0, 30, 104)), -127, 127)]
    return {"sequence_number": seq, "rssi": -55, "noise_floor": -92, "channel": 6, "bandwidth_mhz": 20,
            "subcarrier_count": 52, "provenance": "simulated", "csi_data": {"iq": iq, "src_mac": "24:0A:C4:00:00:01"}}


def run():
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    corp = login("kavitha@wifisense.com", "kavithapassword")
    rooms = call("/rooms", token=fm)[1]
    room = [r for r in rooms if "101" in r["name"]][0]
    mac = "24:0A:C4:EE:%02X:%02X" % tuple(np.random.randint(0, 255, 2))
    st, dev = call("/devices", "POST", {"room_id": room["id"], "mac_address": mac, "device_status": "ONLINE",
                                        "firmware_version": "test", "allowed_source": "simulated"}, fm)
    assert st == 201, dev
    did, tok = dev["id"], dev["hardware_token"]

    print("--- silent device returns nothing")
    st, live = call(f"/sensing/devices/{did}/live", token=fm)
    assert st == 200 and live["has_data"] is False and live["packets"] == [] and live["mode"] == "DEMO", live
    print("[PASS] no packets, DEMO mode")

    rng = np.random.default_rng(7)
    st, body = call("/sensing/ingest", "POST", {"packets": [packet(i, rng) for i in range(30)]}, headers={"X-Device-Token": tok})
    assert st == 201, body

    st, live = call(f"/sensing/devices/{did}/live", token=fm)
    assert st == 200 and live["has_data"] and len(live["packets"]) == 30, live
    assert abs(live["link"]["wavelength_cm"] - 12.30) < 0.05, live["link"]["wavelength_cm"]
    assert live["link"]["center_frequency_mhz"] == 2437.0
    assert len(live["link"]["subcarrier_frequency_mhz"]) == 52
    p0 = live["packets"][0]
    assert len(p0["amplitude"]) == 52 and len(p0["phase"]) == 52 and p0["snr_db"] == 37
    assert p0["meta"]["src_mac"] == "24:0A:C4:00:00:01"
    assert live["stats"]["packet_loss_pct"] == 0.0 and live["stats"]["rssi_mean_dbm"] == -55.0
    forbidden = {"x", "y", "position", "coordinates", "location"}
    assert not forbidden.intersection(live.keys()) and not forbidden.intersection(p0.keys())
    print("[PASS] amplitude/phase per subcarrier, wavelength 12.30 cm, loss 0%, no position fields")

    print("--- incremental polling")
    st, again = call(f"/sensing/devices/{did}/live?after_id={live['latest_id']}", token=fm)
    assert st == 200 and again["packets"] == [] and again["latest_id"] == live["latest_id"]
    call("/sensing/ingest", "POST", {"packets": [packet(30 + i, rng) for i in range(5)]}, headers={"X-Device-Token": tok})
    st, more = call(f"/sensing/devices/{did}/live?after_id={live['latest_id']}", token=fm)
    assert len(more["packets"]) == 5
    print("[PASS] only new packets returned after after_id")

    print("--- packet loss is measured from sequence gaps")
    call("/sensing/ingest", "POST", {"packets": [packet(60, rng), packet(70, rng)]}, headers={"X-Device-Token": tok})
    st, gap = call(f"/sensing/devices/{did}/live", token=fm)
    assert gap["stats"]["packet_loss_pct"] > 0, gap["stats"]
    print("[PASS] gaps reported as loss")

    print("--- another organization cannot see this device")
    st, body = call(f"/sensing/devices/{did}/live", token=corp)
    assert st == 404, (st, body)
    st, _ = call(f"/sensing/devices/{did}/live")
    assert st in (401, 403), st
    print("[PASS] cross-organization 404, anonymous rejected")


if __name__ == "__main__":
    print("=== LIVE CSI STREAM TESTS ===")
    run()
    print("\nALL LIVE STREAM TESTS PASSED")
