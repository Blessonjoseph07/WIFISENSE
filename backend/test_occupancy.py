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
# A person sitting still: the same tiny fluctuation as an empty room, but their body shadows part of the band (different shape).
STILL_BASE = BASE * np.where((np.arange(104) >= 30) & (np.arange(104) < 60), 0.7, 1.0)


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


def send(tok, n, noise, seq0=0, base=None):
    base = BASE if base is None else base
    for i in range(0, n, 50):
        pk = []
        for j in range(i, min(i + 50, n)):
            iq = [int(v) for v in np.clip(np.round(base + RNG.normal(0, noise, 104)), -127, 127)]
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


def check_reconcile():
    """The movement check decides moving vs not moving; the model only chooses within that."""
    from app.routers.occupancy import reconcile
    quiet = {"state": "QUIET", "blocks": [0.05] * 10, "threshold": 0.07}
    moving = {"state": "MOVEMENT", "blocks": [0.09] * 9 + [0.05], "threshold": 0.07}
    walk = {"label": "walking", "text": "Someone walking", "confidence": 0.67, "probabilities": {"empty": 0.1, "still": 0.23, "walking": 0.67}}
    shown, why = reconcile(walk, quiet, False)
    assert shown["label"] == "still" and abs(shown["confidence"] - 0.23 / 0.33) < 0.01 and "does not show" in why, (shown, why)
    still = {"label": "still", "text": "Someone sitting or lying still", "confidence": 0.8, "probabilities": {"still": 0.8, "empty": 0.2}}
    shown, why = reconcile(still, moving, False)
    assert shown["label"] == "presence" and shown["confidence"] == 0.9 and "clear movement" in why, (shown, why)
    shown, why = reconcile(walk, moving, True)
    assert shown["label"] == "walking" and why is None
    print("[PASS] walking is never shown without movement, and still/empty never during clear movement")


def run():
    check_reconcile()
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
    assert ev["method"] == "leave-one-recording-out" and "trained without it" in ev["note"], ev
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

    print("--- someone sitting still is told apart from an empty room (same fluctuation, different signal shape)")
    did3, tok3 = new_device(fm, room)
    for rnd in range(2):
        for label, base in (("empty", BASE), ("still", STILL_BASE)):
            first = latest_id(fm, did3)
            send(tok3, 1000, NOISE["empty"], rnd * 5000, base)
            st, cap = call(f"/sensing/devices/{did3}/occupancy/capture", "POST", {"label": label, "seconds": 5, "from_packet_id": first + 1}, fm)
            assert st == 200, cap
    st, tr = call(f"/sensing/devices/{did3}/occupancy/train", "POST", {}, fm)
    assert st == 200 and tr["evaluation"]["reliable"] is True and tr["evaluation"]["heldout_accuracy"] >= 0.9, tr
    for label, base in (("still", STILL_BASE), ("empty", BASE)):
        send(tok3, 700, NOISE["empty"], 20000, base)
        time.sleep(1.7)
        o = call(f"/sensing/devices/{did3}/occupancy", token=fm)[1]
        assert o["prediction"]["label"] == label, (label, o["prediction"])
    print(f"[PASS] still vs empty: held-out accuracy {tr['evaluation']['heldout_accuracy']}, live predictions follow")

    print("--- one recording per situation: never called reliable, and its confidence is held down")
    did4, tok4 = new_device(fm, room)
    for label in ("empty", "busy"):
        first = latest_id(fm, did4)
        send(tok4, 1000, NOISE[label], 0)
        assert call(f"/sensing/devices/{did4}/occupancy/capture", "POST", {"label": label, "seconds": 5, "from_packet_id": first + 1}, fm)[0] == 200
    st, tr = call(f"/sensing/devices/{did4}/occupancy/train", "POST", {}, fm)
    ev1 = tr["evaluation"]
    assert st == 200 and ev1["method"] == "end-of-recording" and ev1["reliable"] is False and "at least 2 recordings" in ev1["reason"], ev1
    send(tok4, 700, NOISE["busy"], 20000)
    time.sleep(1.7)
    o = call(f"/sensing/devices/{did4}/occupancy", token=fm)[1]
    assert o["prediction"]["label"] == "busy" and o["prediction"]["confidence"] <= 0.81, o["prediction"]
    print(f"[PASS] single recordings: reliable=False ({ev1['reason']}); confidence held to {o['prediction']['confidence']}")
    assert ev["method"] == "leave-one-recording-out", ev
    print("[PASS] with two recordings each, every recording was tested by a model trained without it")

    print("--- the board can read its own state with its device token (for its display)")
    st, own = call("/sensing/device/state", headers={"X-Device-Token": tok3})
    assert st == 200 and own["room_state"]["label"] == "empty" and own["room_state"]["reliable"] is True, own
    assert set(own) == {"presence", "movement_state", "headline", "seconds_since_last_packet", "room_state", "paused"}, own
    assert own["paused"] is False
    assert call("/sensing/device/state")[0] == 401
    assert call("/sensing/device/state", headers={"X-Device-Token": "TK-wrong"})[0] == 401
    print(f"[PASS] device state: {own['headline']} / {own['room_state']['text']}; no token or a wrong token -> 401")

    print("--- pause and resume sensing for one board")
    assert call(f"/sensing/devices/{did3}/pause", "POST", {"paused": True}, care)[0] == 403, "a caregiver must not pause sensing"
    st, pr = call(f"/sensing/devices/{did3}/pause", "POST", {"paused": True}, fm)
    assert st == 200 and pr["paused"] is True, pr
    own = call("/sensing/device/state", headers={"X-Device-Token": tok3})[1]
    assert own["paused"] is True and own["movement_state"] == "PAUSED" and own["room_state"] is None, own
    assert call(f"/sensing/devices/{did3}/movement", token=fm)[1]["state"] == "PAUSED"
    assert call(f"/sensing/devices/{did3}/live", token=fm)[1]["paused"] is True
    st, pr = call(f"/sensing/devices/{did3}/pause", "POST", {"paused": False}, fm)
    own = call("/sensing/device/state", headers={"X-Device-Token": tok3})[1]
    assert st == 200 and own["paused"] is False and own["movement_state"] != "PAUSED", own
    print("[PASS] pause: board state, movement and live view all say PAUSED (caregiver refused); resume clears it")

    print("--- reset")
    st, _ = call(f"/sensing/devices/{did}/occupancy", "DELETE", None, fm)
    st, o = call(f"/sensing/devices/{did}/occupancy", token=fm)
    assert st == 200 and o["trained"] is False and o["samples"]["busy"]["blocks"] == 0, o
    print("[PASS] reset removes samples and the model")
    print("\nALL OCCUPANCY LEARNER TESTS PASSED")


if __name__ == "__main__":
    run()
