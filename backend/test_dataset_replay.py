"""
Dataset replay, detection and provenance tests.

Runs against a live seeded server (API_BASE, default http://127.0.0.1:8000) and the same DATABASE_URL for setup,
cleanup and a few in-process checks. All packets here are SYNTHETIC random numbers made for the test. No real dataset
is needed or stored in the repository. The tests check the pipeline's rules (provenance, windowing, labels, scoping,
alerts), not the model's accuracy; accuracy is measured separately in experiments/wifall.
"""
import json
import os
import urllib.error
import urllib.request
from unittest import mock

import numpy as np
from sqlmodel import Session, select

from app.core.database import engine
from app.models.entities import (
    Alert, AlertAcknowledgement, Building, Floor, Organization, RawCsiTelemetry, ReplayEvaluation, Room,
    SensingDevice, SensingEvent,
)
from app.services import csi_features, detection, fall_model

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def api_call(endpoint, method="GET", data=None, token=None, device_token=None):
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(f"{API_BASE}{endpoint}", data=req_data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if device_token:
        req.add_header("X-Device-Token", device_token)
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


def synthetic_iq(n, seed):
    return np.random.default_rng(seed).integers(-30, 30, size=(n, 104))


def packets(iq, seq0=1000, rssi=-40, noise=-99, fmt="iq"):
    out = []
    for i, row in enumerate(iq):
        csi = {"iq": [int(v) for v in row]} if fmt == "iq" else {"subcarriers": [float(v) for v in row[:56]]}
        out.append(dict(sequence_number=seq0 + i, rssi=rssi, noise_floor=noise, subcarrier_count=52 if fmt == "iq" else 56,
                        bandwidth_mhz=20, channel=12, csi_data=csi))
    return out


def post_packets(device_token, pkts, batch=60):
    responses = []
    for i in range(0, len(pkts), batch):
        status, res = api_call("/sensing/ingest", "POST", {"packets": pkts[i:i + batch]}, device_token=device_token)
        assert status == 201, f"ingest failed: {status} {res}"
        responses.append(res)
    return responses


def run_tests():
    print("=== RUNNING DATASET REPLAY / DETECTION / PROVENANCE TESTS (synthetic packets only) ===")
    admin = login("blesson@wifisense.com", "blessonpassword")
    care_admin = login("anjali@wifisense.com", "anjalipassword")
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")

    with Session(engine) as session:
        room = session.exec(select(Room).join(Floor).join(Building).join(Organization)
                            .where(Organization.type == "ELDER_CARE")).first()
        room_id = room.id
        seeded_demo = session.exec(select(SensingDevice).where(SensingDevice.room_id == room_id)).first()
        seeded_demo_id = seeded_demo.id

    created_devices = []

    def make_device(mac, source):
        status, dev = api_call("/devices", "POST", {"room_id": room_id, "mac_address": mac, "device_status": "OFFLINE",
                                                     "allowed_source": source}, admin)
        assert status in (200, 201), f"{status} {dev}"
        created_devices.append(dev["id"])
        return dev["id"], dev["hardware_token"]

    try:
        ds_id, ds_tok = make_device("DE:AD:BE:EF:02:01", "dataset")
        ds2_id, ds2_tok = make_device("DE:AD:BE:EF:02:02", "dataset")
        demo_id, demo_tok = make_device("DE:AD:BE:EF:02:03", "simulated")
        empty_id, _ = make_device("DE:AD:BE:EF:02:04", "dataset")

        # ------------------------------------------------------------------ 1. model information
        print("\n--- 1. Model information states its limits ---")
        status, info = api_call("/sensing/model-info", token=care_admin)
        assert status == 200 and info["available"] is True, info
        assert info["evaluation"]["person_averaged_balanced_accuracy"] < 0.75, "must report the person-independent figure"
        assert any("verification" in l.lower() for l in info["limitations"]), info["limitations"]
        assert "NOT" in info["score_meaning"]
        print(f"[PASS] Model info available: person-independent balanced accuracy "
              f"{info['evaluation']['person_averaged_balanced_accuracy']}, score documented as uncalibrated.")

        # ------------------------------------------------------------------ 2. replay a clip
        print("\n--- 2. Replaying a recorded clip through /sensing/ingest ---")
        status, alerts_before = api_call("/alerts", token=care_admin)
        clip = synthetic_iq(285, seed=1)
        responses = post_packets(ds_tok, packets(clip))
        assert all(r["provenance"] == "dataset" and r["detections"] == [] for r in responses), \
            "No window is complete before 300 packets"
        status, det = api_call("/sensing/detect", "POST", {}, device_token=ds_tok)
        assert status == 200 and len(det["detections"]) == 1, det
        d = det["detections"][0]
        assert d["source"] == "dataset" and d["window_packets"] == 285, d
        assert d["activity"] in ("Possible_Fall", "No_Fall_Pattern"), d
        assert 0.0 <= d["fall_score"] <= 1.0 and 0.5 <= d["confidence"] <= 1.0, d
        assert d["alert_id"] is None, "DATASET REPLAY must never raise alerts"
        event1 = d["event_id"]
        status, alerts_after = api_call("/alerts", token=care_admin)
        assert len(alerts_after) == len(alerts_before), "Replay created an alert!"
        print(f"[PASS] 285 packets -> one detection ({d['activity']}, score {d['fall_score']}), "
              "provenance dataset, no alert raised.")

        status, det = api_call("/sensing/detect", "POST", {}, device_token=ds_tok)
        assert det["detections"] == [], "Packets must not be analysed twice"
        print("[PASS] A second flush analyses nothing: packets are consumed once.")

        responses = post_packets(ds_tok, packets(synthetic_iq(600, seed=2), seq0=5000))
        found = [x for r in responses for x in r["detections"]]
        assert len(found) == 2 and all(x["window_packets"] == 300 for x in found), found
        print("[PASS] A continuous stream of 600 packets completes two 300-packet windows automatically.")

        post_packets(ds_tok, packets(synthetic_iq(50, seed=3), seq0=9000))
        status, det = api_call("/sensing/detect", "POST", {}, device_token=ds_tok)
        assert det["detections"] == [] and "fewer than" in (det["note"] or "").lower(), det
        print("[PASS] A fragment of 50 packets is not analysed (noted, not guessed).")

        # ------------------------------------------------------------------ 3. rules
        print("\n--- 3. Provenance and format rules ---")
        resp = post_packets(demo_tok, packets(synthetic_iq(300, seed=4)))
        assert all(r["detections"] == [] for r in resp)
        assert "DEMO" in (resp[-1]["detection_note"] or ""), resp[-1]
        with Session(engine) as session:
            n_events = session.exec(select(SensingEvent).where(SensingEvent.device_id == demo_id)).all()
            assert n_events == [], "A DEMO device must never receive a model result"
        print("[PASS] DEMO device: packets stored, no model result, and the note says why.")

        resp = post_packets(ds2_tok, packets(synthetic_iq(300, seed=5), fmt="other"))
        assert all(r["detections"] == [] for r in resp)
        assert "not supported" in (resp[-1]["detection_note"] or "").lower(), resp[-1]
        with Session(engine) as session:
            rows = session.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == ds2_id)).all()
            assert rows and all(r.event_id == -1 for r in rows), "Unsupported packets must be marked skipped"
        print("[PASS] Unsupported CSI format: stored, skipped, never guessed.")

        bad = packets(synthetic_iq(5, seed=6))
        bad[0]["label"] = "fall"
        status, res = api_call("/sensing/ingest", "POST", {"packets": bad}, device_token=ds_tok)
        assert status == 422
        bad = packets(synthetic_iq(5, seed=6))
        bad[0]["csi_data"]["label"] = "fall"
        status, res = api_call("/sensing/ingest", "POST", {"packets": bad}, device_token=ds_tok)
        assert status == 422
        print("[PASS] Ground-truth labels are rejected in packets, at top level and inside csi_data.")

        # ------------------------------------------------------------------ 4. history
        print("\n--- 4. Detection history shows the mode and the evidence ---")
        status, hist = api_call("/sensing/history?source=dataset&limit=20", token=care_admin)
        assert status == 200
        mine = next(h for h in hist if h["id"] == event1)
        assert mine["source"] == "dataset" and mine["model"] == "wifall_rf_v2", mine
        assert mine["subcarrier_count"] == 52 and mine["window_packets"] == 285 and mine["noise_floor"] == -99.0, mine
        assert mine["device_mac"] == "DE:AD:BE:EF:02:01" and mine["recorded_label"] is None, mine
        if mine["activity"] == "Possible_Fall":
            assert mine["requires_verification"] is True
        status, corp = api_call("/sensing/history?source=dataset&limit=200", token=corp_fm)
        assert status == 200 and not any(h["id"] == event1 for h in corp), "Corporate user sees elder-care replay!"
        status, res = api_call("/sensing/history?source=bogus", token=care_admin)
        assert status == 422
        print("[PASS] History lists the replay window with model, packets, noise, subcarriers and device; "
              "corporate users cannot see it; bad filter rejected.")

        # ------------------------------------------------------------------ 5. ground truth
        print("\n--- 5. Ground-truth labels are separate, admin-only and scoped ---")
        evs = [event1] + [x["event_id"] for x in found]
        body = {"event_id": event1, "recorded_label": "fall", "dataset_name": "SYNTHETIC-TEST"}
        status, res = api_call("/sensing/replay/evaluations", "POST", body, device_token=ds_tok)
        assert status in (401, 403), f"A device must not write labels, got {status}"
        status, res = api_call("/sensing/replay/evaluations", "POST", body, token=corp_fm)
        assert status in (403, 404), f"Corporate user wrote a label: {status}"
        try:
            caregiver = login("mary@wifisense.com", "marypassword")
            status, res = api_call("/sensing/replay/evaluations", "POST", body, token=caregiver)
            assert status == 403, f"Caregiver must not write labels, got {status}"
            print("[PASS] Caregiver cannot write labels (403).")
        except AssertionError as exc:
            if "Login failed" not in str(exc):
                raise
        print("[PASS] Devices and corporate users cannot write ground truth.")

        status, res = api_call("/sensing/replay/evaluations", "POST", body, token=care_admin)
        assert status == 201, f"{status} {res}"
        status, res = api_call("/sensing/replay/evaluations", "POST", body, token=care_admin)
        assert status == 409
        status, res = api_call("/sensing/replay/evaluations", "POST", dict(body, event_id=99999999), token=care_admin)
        assert status == 404
        status, res = api_call("/sensing/replay/evaluations", "POST", dict(body, extra="x"), token=care_admin)
        assert status == 422
        status, res = api_call("/sensing/replay/evaluations", "POST", dict(body, recorded_label="x" * 41), token=care_admin)
        assert status == 422
        print("[PASS] Label recorded once (409 on repeat); unknown event 404; extra field and long label rejected (422).")

        status, sim = api_call("/sensing/simulate-event", "POST",
                               {"device_id": seeded_demo_id, "simulated_activity": "Walking"}, care_admin)
        assert status == 201
        sim_event = sim["sensing_event"]["id"]
        status, res = api_call("/sensing/replay/evaluations", "POST", dict(body, event_id=sim_event), token=care_admin)
        assert status == 400, f"Labels only attach to DATASET events, got {status}"
        print("[PASS] A label cannot be attached to a DEMO event (400).")

        for ev, label in zip(evs[1:], ["walk", "fall"]):
            status, res = api_call("/sensing/replay/evaluations", "POST", dict(body, event_id=ev, recorded_label=label), token=care_admin)
            assert status == 201
        status, hist = api_call("/sensing/history?source=dataset&limit=20", token=care_admin)
        labels = {h["id"]: h for h in hist}
        assert labels[event1]["recorded_label"] == "fall"

        status, summ = api_call("/sensing/replay/summary", token=care_admin)
        assert status == 200 and summ["windows_evaluated"] == 3, summ
        tp = fn = fp = tn = 0
        for ev, lab in zip(evs, ["fall", "walk", "fall"]):
            flagged = labels[ev]["activity"] == "Possible_Fall"
            if lab == "fall":
                tp += flagged
                fn += not flagged
            else:
                fp += flagged
                tn += not flagged
        assert (summ["possible_fall_flagged_on_recorded_falls"], summ["missed_recorded_falls"],
                summ["false_alarms_on_recorded_non_falls"], summ["correct_non_falls"]) == (tp, fn, fp, tn), (summ, tp, fn, fp, tn)
        assert "REPLAYED" in summ["statement"] and "live" in summ["statement"].lower()
        status, summ_corp = api_call("/sensing/replay/summary", token=corp_fm)
        assert status == 200 and summ_corp["windows_evaluated"] == 0, "Corporate user sees elder-care evaluations!"
        print("[PASS] Summary counts match the detector's own results vs the recorded labels, states it is replay "
              "only, and is empty for corporate users.")

        # ------------------------------------------------------------------ 6. truthful telemetry
        print("\n--- 6. Device telemetry reports only what was really received ---")
        status, t = api_call(f"/sensing/devices/{empty_id}/csi-telemetry", token=care_admin)
        assert status == 200 and t["has_data"] is False and t["packets_total"] == 0 and t["mode"] == "DATASET REPLAY", t
        assert "last_packet" not in t and "amplitude_last_packet" not in t and t["latest_detection"] is None, t
        status, t = api_call(f"/sensing/devices/{seeded_demo_id}/csi-telemetry", token=care_admin)
        assert t["mode"] == "DEMO" and t["has_data"] is False and "Demonstration" in t["data_statement"], t
        print("[PASS] A device with no packets reports none (no invented spectrum, RSSI or calibration).")

        status, t = api_call(f"/sensing/devices/{ds_id}/csi-telemetry", token=care_admin)
        assert t["has_data"] is True and t["mode"] == "DATASET REPLAY", t
        assert t["last_packet"]["rssi_dbm"] == -40 and t["last_packet"]["noise_floor_dbm"] == -99, t["last_packet"]
        assert t["last_packet"]["subcarrier_count"] == 52 and len(t["amplitude_last_packet"]) == 52
        assert t["recent_window"]["rssi_median_dbm"] == -40.0 and t["latest_detection"]["source"] == "dataset"
        assert "not current sensing" in t["data_statement"]
        print("[PASS] Telemetry equals what was posted (RSSI, noise, 52 subcarriers) and says it is a replay.")

        status, t = api_call(f"/sensing/devices/{ds_id}/csi-telemetry", token=corp_fm)
        assert status == 404, f"Corporate user read an elder-care device's telemetry: {status}"
        status, t = api_call("/sensing/devices/does-not-exist/csi-telemetry", token=care_admin)
        assert status == 404
        print("[PASS] Telemetry is organization-scoped: corporate users and unknown ids get 404.")

        # ------------------------------------------------------------------ 7. in-process: live rules
        print("\n--- 7. LIVE HARDWARE rules (detector scores forced, in-process) ---")
        with Session(engine) as session:
            live = SensingDevice(mac_address="DE:AD:BE:EF:02:05", room_id=room_id, device_status="ONLINE",
                                 allowed_source="live", hardware_token_hash="x" * 64)
            session.add(live)
            session.commit()
            session.refresh(live)
            created_devices.append(live.id)
            live_id = live.id

            def insert(device, n, seed, seq0):
                for i, row in enumerate(synthetic_iq(n, seed)):
                    session.add(RawCsiTelemetry(device_id=device.id, room_id=room_id, sequence_number=seq0 + i, rssi=-40,
                                                noise_floor=-99, subcarrier_count=52, bandwidth_mhz=20, channel=12,
                                                csi_data={"iq": [int(v) for v in row]}, provenance=device.allowed_source))
                session.commit()

            insert(live, 300, 7, 100)
            with mock.patch.object(fall_model, "fall_score", return_value=0.93):
                out = detection.run_detection(session, live)
            assert len(out["detections"]) == 1 and out["detections"][0]["fall_suspected"] is True
            alert_id = out["detections"][0]["alert_id"]
            assert alert_id, "LIVE possible fall must raise an alert"
            alert = session.get(Alert, alert_id)
            assert alert.source == "live" and "[LIVE HARDWARE]" in alert.message and "verification required" in alert.message
            assert alert.confidence == 0.93 and alert.event_type == "Fall_Detected"
            insert(live, 300, 8, 1000)
            with mock.patch.object(fall_model, "fall_score", return_value=0.97):
                out2 = detection.run_detection(session, live)
            assert out2["detections"][0]["alert_id"] is None, "Second window inside the dedupe period must not alert again"
        status, a = api_call(f"/alerts/{alert_id}", token=care_admin)
        assert status == 200 and a["source"] == "live" and a["confidence_level"] == "HIGH", a
        assert a["requires_verification"] is True, "A model-detected fall always needs verification, even at a high score"
        status, v = api_call(f"/alerts/{alert_id}/verify", "PATCH", {"outcome": "DISMISSED", "note": "synthetic test"}, care_admin)
        assert status == 200 and v["verification_status"] == "DISMISSED"
        print("[PASS] LIVE possible fall: alert says [LIVE HARDWARE] and 'verification required', needs verification even at "
              "score 0.93, is not repeated within the dedupe period, and can be dismissed by staff.")

        with Session(engine) as session:
            dev = session.get(SensingDevice, ds_id)
            for i, row in enumerate(synthetic_iq(300, 9)):
                session.add(RawCsiTelemetry(device_id=ds_id, room_id=room_id, sequence_number=20000 + i, rssi=-40, noise_floor=-99,
                                            subcarrier_count=52, bandwidth_mhz=20, channel=12,
                                            csi_data={"iq": [int(v) for v in row]}, provenance="dataset"))
            session.commit()
            with mock.patch.object(fall_model, "fall_score", return_value=0.88):
                out3 = detection.run_detection(session, dev)
            assert out3["detections"][0]["fall_suspected"] and out3["detections"][0]["alert_id"] is None
            for i, row in enumerate(synthetic_iq(300, 10)):
                session.add(RawCsiTelemetry(device_id=ds_id, room_id=room_id, sequence_number=30000 + i, rssi=-40, noise_floor=-99,
                                            subcarrier_count=52, bandwidth_mhz=20, channel=12,
                                            csi_data={"iq": [int(v) for v in row]}, provenance="dataset"))
            session.commit()
            with mock.patch.object(fall_model, "fall_score", return_value=0.2):
                out4 = detection.run_detection(session, dev)
            d4 = out4["detections"][0]
            assert d4["activity"] == "No_Fall_Pattern" and abs(d4["confidence"] - 0.8) < 1e-6, d4
        print("[PASS] DATASET possible fall raises no alert; a low score becomes No_Fall_Pattern with confidence 1 - score.")

        # ------------------------------------------------------------------ 8. units
        print("\n--- 8. Signal quality and features ---")
        q = detection.signal_quality([-30] * 10, [-99] * 10, list(range(10)))
        assert q["quality"] >= 95 and q["completeness"] == 1.0, q
        q = detection.signal_quality([-40] * 10, [-99] * 10, [0, 2, 4, 6, 8, 10, 12, 14, 16, 18])
        assert q["completeness"] < 0.6 and q["quality"] < 85, q
        q = detection.signal_quality([-40] * 10, [], list(range(10)))
        assert q["quality"] is None and q["snr_db"] is None, "Unknown noise floor means unknown quality"
        q = detection.signal_quality([-95] * 10, [-99] * 10, list(range(10)))
        assert q["quality"] < 50, q
        names, vec = csi_features.extract_features(synthetic_iq(250, 11))
        assert len(names) == 38 and np.all(np.isfinite(vec))
        for bad_input in (synthetic_iq(50, 12), np.zeros((250, 90))):
            try:
                csi_features.extract_features(bad_input)
                raise AssertionError("bad input accepted")
            except ValueError:
                pass
        print("[PASS] Signal quality is None when unknown, drops with gaps or low SNR; features are finite and reject bad input.")
    finally:
        print("\n--- Cleanup ---")
        with Session(engine) as session:
            ids = list(created_devices)
            ev_ids = [e.id for e in session.exec(select(SensingEvent).where(SensingEvent.device_id.in_(ids))).all()] if ids else []
            for row in session.exec(select(ReplayEvaluation).where(ReplayEvaluation.device_id.in_(ids))).all() if ids else []:
                session.delete(row)
            session.commit()
            for row in session.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id.in_(ids))).all() if ids else []:
                session.delete(row)
            for al in session.exec(select(Alert).where(Alert.device_id.in_(ids))).all() if ids else []:
                for ack in session.exec(select(AlertAcknowledgement).where(AlertAcknowledgement.alert_id == al.id)).all():
                    session.delete(ack)
                session.delete(al)
            session.commit()
            for eid in ev_ids:
                e = session.get(SensingEvent, eid)
                if e:
                    session.delete(e)
            for sim in session.exec(select(SensingEvent).where(SensingEvent.id == (sim_event if 'sim_event' in dir() else -1))).all():
                session.delete(sim)
            session.commit()
            for did in ids:
                d = session.get(SensingDevice, did)
                if d:
                    session.delete(d)
            session.commit()
        print(f"[PASS] Removed {len(created_devices)} test devices and their packets, events, labels and alerts.")

    print("\n========================================================")
    print("ALL DATASET REPLAY & DETECTION TESTS PASSED SUCCESSFULLY")
    print("========================================================")


if __name__ == "__main__":
    run_tests()
