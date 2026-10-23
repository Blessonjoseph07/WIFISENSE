"""
MOVEMENT INDICATOR TEST
=======================
GET /sensing/devices/{id}/movement and POST .../movement/baseline: the signal-fluctuation indicator for the Live Hardware view.
Uses a device registered as simulated (stored as DEMO) with synthetic packets, so no real hardware is needed. Checks that it never
judges without a baseline, separates quiet from movement, refuses an unstable baseline, keeps the access rules, and reports a
silent board as such.
"""
import json
import os
import time
import urllib.error
import urllib.request
import uuid

import numpy as np

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
RNG = np.random.default_rng(11)


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
    st, body = call("/auth/login", "POST", {"email": email, "password": password})
    assert st == 200, body
    return body["access_token"]


BASE = RNG.uniform(25, 45, 104)


def packet(seq, noise):
    iq = [int(v) for v in np.clip(np.round(BASE + RNG.normal(0, noise, 104)), -127, 127)]
    return {"sequence_number": seq, "rssi": -55, "noise_floor": -92, "channel": 6, "bandwidth_mhz": 20, "subcarrier_count": 52,
            "provenance": "simulated", "csi_data": {"iq": iq}}


def send(tok, start, count, noise):
    for i in range(start, start + count, 50):
        st, body = call("/sensing/ingest", "POST", {"packets": [packet(j, noise) for j in range(i, min(i + 50, start + count))]},
                        headers={"X-Device-Token": tok})
        assert st == 201, body


def run():
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    care = login("mary@wifisense.com", "marypassword")
    corp = login("abhinand@wifisense.com", "abhinandpassword")
    room = [r for r in call("/rooms", token=fm)[1] if "101" in r["name"]][0]
    mac = "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3])
    st, dev = call("/devices", "POST", {"room_id": room["id"], "mac_address": mac, "device_status": "ONLINE",
                                        "firmware_version": "test", "allowed_source": "simulated"}, fm)
    assert st == 201, dev
    did, tok = dev["id"], dev["hardware_token"]

    print("--- no data, then no baseline")
    st, m = call(f"/sensing/devices/{did}/movement", token=fm)
    assert st == 200 and m["state"] == "NO_DATA" and m["mode"] == "DEMO", m
    send(tok, 0, 400, 1.5)                                  # quiet readings
    time.sleep(1.7)                                         # the result is cached for ~1.5 s
    st, m = call(f"/sensing/devices/{did}/movement", token=fm)
    assert m["state"] == "NO_BASELINE" and m["threshold"] is None and m["blocks"], m
    assert any("does not count" in c for c in m["caveats"]) and any("standing" in c for c in m["caveats"])
    print("[PASS] without a baseline the state is NO_BASELINE (no judgement), and the limits are stated")

    print("--- access rules")
    st, _ = call(f"/sensing/devices/{did}/movement/baseline", "POST", {}, care)
    assert st == 403, "a caregiver must not record a baseline"
    st, _ = call(f"/sensing/devices/{did}/movement", token=corp)
    assert st == 404, "another organization must not see this device"
    print("[PASS] caregiver gets 403 on the baseline; another organization gets 404")

    print("--- baseline and quiet")
    st, b = call(f"/sensing/devices/{did}/movement/baseline", "POST", {}, fm)
    assert st == 200 and b["baseline"]["blocks"] >= 6 and b["baseline"]["threshold"] > b["baseline"]["mean"], b
    send(tok, 400, 200, 1.5)
    st, m = call(f"/sensing/devices/{did}/movement", token=fm)
    time.sleep(1.7)  # the result is cached for ~1.5 s
    st, m = call(f"/sensing/devices/{did}/movement", token=fm)
    assert m["state"] == "QUIET", m
    print(f"[PASS] with an empty-room baseline (threshold {b['baseline']['threshold']}) the same kind of signal reads QUIET")

    print("--- presence (held above the empty-room level, without strong movement)")
    send(tok, 600, 700, 1.9)                                # modestly elevated for ~14 blocks
    time.sleep(1.7)
    st, m = call(f"/sensing/devices/{did}/movement", token=fm)
    assert m["state"] == "PRESENT" and m["presence"] is True and 1.15 < m["activity_ratio"] < 1.6, m
    print(f"[PASS] a signal held {m['activity_ratio']}x above the empty-room level reads PRESENT (presence likely), not MOVEMENT")

    print("--- movement")
    send(tok, 1300, 200, 14)                                 # strongly fluctuating readings
    time.sleep(1.7)
    st, m = call(f"/sensing/devices/{did}/movement", token=fm)
    assert m["state"] == "MOVEMENT" and max(m["blocks"][-3:]) > m["threshold"], m
    print("[PASS] a strongly fluctuating signal reads MOVEMENT")

    print("--- live hardware: fall detection is off by default")
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.entities import RawCsiTelemetry, SensingEvent
    live = call("/devices", "POST", {"room_id": room["id"], "mac_address": "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3]),
                                     "device_status": "ONLINE", "firmware_version": "t", "allowed_source": "live"}, fm)[1]
    pk = lambda i: {**packet(i, 3), "provenance": "live"}
    st, body = call("/sensing/ingest", "POST", {"packets": [pk(i) for i in range(50)]}, headers={"X-Device-Token": live["hardware_token"]})
    assert st == 201
    for k in range(50, 350, 50):
        st, body = call("/sensing/ingest", "POST", {"packets": [pk(i) for i in range(k, k + 50)]}, headers={"X-Device-Token": live["hardware_token"]})
    assert st == 201 and body["detections"] == [] and "switched off" in (body["detection_note"] or ""), body
    with Session(engine) as ses:
        left = ses.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == live["id"], RawCsiTelemetry.event_id.is_(None))).all()
        evs = ses.exec(select(SensingEvent).where(SensingEvent.device_id == live["id"])).all()
    assert not left and not evs, (len(left), len(evs))
    time.sleep(1.7)
    st, mv = call(f"/sensing/devices/{live['id']}/movement", token=fm)
    assert st == 200 and mv["mode"] == "LIVE HARDWARE" and mv["fall_detection"].startswith("off"), mv
    print("[PASS] 350 live packets: no fall detection, no events, none left 'pending' (they can age out), and the API says so")

    print("--- an unstable baseline is refused")
    st, bad = call(f"/sensing/devices/{did}/movement/baseline", "POST", {}, fm)
    assert st in (200, 409), bad
    dev2 = call("/devices", "POST", {"room_id": room["id"], "mac_address": "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3]),
                                     "device_status": "ONLINE", "firmware_version": "t", "allowed_source": "simulated"}, fm)[1]
    send(dev2["hardware_token"], 0, 150, 1.5)
    send(dev2["hardware_token"], 150, 150, 25)
    st, bad = call(f"/sensing/devices/{dev2['id']}/movement/baseline", "POST", {}, fm)
    assert st == 409 and "too much" in bad["detail"], (st, bad)
    print("[PASS] a baseline recorded while the signal was jumping around is refused with a clear message")

    print("--- not enough readings")
    dev3 = call("/devices", "POST", {"room_id": room["id"], "mac_address": "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3]),
                                     "device_status": "ONLINE", "firmware_version": "t", "allowed_source": "simulated"}, fm)[1]
    send(dev3["hardware_token"], 0, 100, 1.5)
    st, bad = call(f"/sensing/devices/{dev3['id']}/movement/baseline", "POST", {}, fm)
    assert st == 409 and "Not enough" in bad["detail"], (st, bad)
    print("[PASS] too few packets: refused, nothing saved")

    print("\nALL MOVEMENT INDICATOR TESTS PASSED")


if __name__ == "__main__":
    run()
