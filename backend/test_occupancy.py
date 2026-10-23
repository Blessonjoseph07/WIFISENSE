"""
OCCUPANCY LEARNER TEST (Phase 2)
================================
Record labelled segments, train, predict, and be honest about it. Uses a simulated device and synthetic packets whose noise level
stands in for an empty / a few people / a busy room. Checks: access rules, refusal to train without data, a reliable model on
separable data with a held-out accuracy, live predictions that follow the signal, and NOT claiming reliability when the situations
cannot be told apart.
"""
import json
import os
import time
import urllib.error
import urllib.request
import uuid

import numpy as np

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
RNG = np.random.default_rng(21)
BASE = RNG.uniform(25, 45, 104)
NOISE = {"empty": 1.0, "few": 2.6, "busy": 7.0}


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


def send(tok, n, noise, seq0=0):
    for i in range(0, n, 50):
        pk = []
        for j in range(i, min(i + 50, n)):
            iq = [int(v) for v in np.clip(np.round(BASE + RNG.normal(0, noise, 104)), -127, 127)]
            pk.append({"sequence_number": seq0 + j, "rssi": int(-50 + RNG.normal(0, max(0.3, noise / 3))), "noise_floor": -92, "channel": 6,
                       "bandwidth_mhz": 20, "subcarrier_count": 52, "provenance": "simulated", "csi_data": {"iq": iq}})
        st, body = call("/sensing/ingest", "POST", {"packets": pk}, headers={"X-Device-Token": tok})
        assert st == 201, body


def latest_id(fm, did):
    return call(f"/sensing/devices/{did}/live", token=fm)[1]["latest_id"]


def new_device(fm, room):
    mac = "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3])
    st, dev = call("/devices", "POST", {"room_id": room["id"], "mac_address": mac, "device_status": "ONLINE", "firmware_version": "t",
                                        "allowed_source": "simulated"}, fm)
    assert st == 201, dev
    return dev["id"], dev["hardware_token"]


def run():
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    care = login("mary@wifisense.com", "marypassword")
    corp = login("abhinand@wifisense.com", "abhinandpassword")
    room = [r for r in call("/rooms", token=fm)[1] if "101" in r["name"]][0]
    did, tok = new_device(fm, room)

    print("--- nothing to learn from yet")
    st, o = call(f"/sensing/devices/{did}/occupancy", token=fm)
    assert st == 200 and o["trained"] is False and o["can_train"] is False and o["prediction_state"] == "NO_MODEL", o
    st, e = call(f"/sensing/devices/{did}/occupancy/train", "POST", {}, fm)
    assert st == 409 and "at least two situations" in e["detail"], e
    print("[PASS] untrained: no prediction, training refused with a plain reason")

    print("--- access rules")
    st, _ = call(f"/sensing/devices/{did}/occupancy/capture", "POST", {"label": "busy", "seconds": 5}, care)
    assert st == 403
    st, _ = call(f"/sensing/devices/{did}/occupancy", token=corp)
    assert st == 404
    st, bad = call(f"/sensing/devices/{did}/occupancy/capture", "POST", {"label": "crowded", "seconds": 5}, fm)
    assert st == 422
    print("[PASS] a caregiver cannot record (403), another organization gets 404, unknown labels are rejected (422)")

    print("--- recording labelled segments")
    for rnd in range(2):
        for label in ("empty", "few", "busy"):
            first = latest_id(fm, did)
            send(tok, 1000, NOISE[label], rnd * 5000)
            st, cap = call(f"/sensing/devices/{did}/occupancy/capture", "POST", {"label": label, "seconds": 5, "from_packet_id": first + 1}, fm)
            assert st == 200 and cap["blocks_saved"] >= 19, (label, st, cap)
    st, o = call(f"/sensing/devices/{did}/occupancy", token=fm)
    assert o["can_train"] and all(o["samples"][l]["sessions"] == 2 for l in ("empty", "few", "busy")), o["samples"]
    print(f"[PASS] six segments recorded: {o['samples']}")

    print("--- training and honest evaluation")
    st, tr = call(f"/sensing/devices/{did}/occupancy/train", "POST", {}, fm)
    ev = tr["evaluation"]
    assert st == 200 and ev["reliable"] is True and ev["heldout_accuracy"] >= 0.9, ev
    assert all(v >= 6 for v in ev["heldout_blocks"].values()) and ev["majority_baseline"] < 0.5, ev
    assert "never used to train" in ev["note"]
    print(f"[PASS] held-out accuracy {ev['heldout_accuracy']} on blocks never used for training (majority guess would be {ev['majority_baseline']}); reliable={ev['reliable']}")

    print("--- live predictions follow the signal")
    for label in ("busy", "empty", "few"):
        send(tok, 700, NOISE[label], 20000)
        time.sleep(1.7)                                     # the answer is cached for ~1.5 s
        st, o = call(f"/sensing/devices/{did}/occupancy", token=fm)
        assert st == 200 and o["prediction_state"] == "READY" and o["prediction"]["label"] == label, (label, o["prediction"], o["prediction_state"])
        assert o["prediction"]["confidence"] > 0.6
        print(f"[PASS] signal like '{label}' -> predicted {o['prediction']['text']} ({o['prediction']['confidence']})")

    print("--- it must not claim reliability when the situations cannot be told apart")
    did2, tok2 = new_device(fm, room)
    for _ in range(2):
        for label in ("empty", "busy"):
            first = latest_id(fm, did2)
            send(tok2, 1000, 3.0, 0)                        # identical signal labelled differently
            assert call(f"/sensing/devices/{did2}/occupancy/capture", "POST", {"label": label, "seconds": 5, "from_packet_id": first + 1}, fm)[0] == 200
    st, tr = call(f"/sensing/devices/{did2}/occupancy/train", "POST", {}, fm)
    assert st == 200 and tr["evaluation"]["reliable"] is False and "did not separate" in tr["evaluation"]["reason"], tr
    print(f"[PASS] identical signals labelled differently: held-out accuracy {tr['evaluation']['heldout_accuracy']}, reliable=False ({tr['evaluation']['reason']})")

    print("--- reset")
    st, _ = call(f"/sensing/devices/{did}/occupancy", "DELETE", None, fm)
    st, o = call(f"/sensing/devices/{did}/occupancy", token=fm)
    assert st == 200 and o["trained"] is False and o["samples"]["busy"]["blocks"] == 0, o
    print("[PASS] reset removes samples and the model")
    print("\nALL OCCUPANCY LEARNER TESTS PASSED")


if __name__ == "__main__":
    run()
