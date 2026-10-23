"""
RAW CSI RETENTION TEST SUITE
============================
raw_csi_telemetry is a rolling window. Analysed packets older than the retention window are deleted, the oldest
analysed packets go first when the table passes its row cap, and packets the detector has NOT processed yet are never
deleted by the age rule. Detection results (sensing_events) are untouched. Runs against DATABASE_URL like the other
database-level tests, plus the /sensing/retention endpoint on a running server.
"""
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.database import engine
from app.models.entities import RawCsiTelemetry, SensingDevice, SensingEvent
from app.services.retention import prune_raw_csi, retention_status

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
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    care = login("mary@wifisense.com", "marypassword")
    rooms = call("/rooms", token=fm)[1]
    room = [r for r in rooms if "101" in r["name"]][0]
    mac = "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3])
    st, dev = call("/devices", "POST", {"room_id": room["id"], "mac_address": mac, "device_status": "ONLINE",
                                        "firmware_version": "test", "allowed_source": "simulated"}, fm)
    assert st == 201, dev
    device_id = dev["id"]
    now = datetime.now(timezone.utc)

    def packet(age_hours, event_id):
        t = now - timedelta(hours=age_hours)
        return RawCsiTelemetry(device_id=device_id, room_id=room["id"], timestamp=t, created_at=t, rssi=-55,
                               csi_data={"iq": [0] * 104}, provenance="simulated", event_id=event_id)

    created = []
    try:
        with Session(engine) as s:
            ev = SensingEvent(device_id=device_id, room_id=room["id"], rssi=-55, subcarrier_count=52, signal_quality=90,
                              event_type="DetectionWindow", extracted_features={}, inferred_activity_id=1, model_confidence=0.9, source="simulated")
            s.add(ev); s.commit(); s.refresh(ev)
            ev_id = ev.id
            rows = ([packet(30, ev_id) for _ in range(5)]      # old and analysed      -> deleted
                    + [packet(30, -1) for _ in range(3)]       # old and skipped       -> deleted
                    + [packet(30, None) for _ in range(4)]     # old but UNPROCESSED   -> kept
                    + [packet(2, ev_id) for _ in range(6)])    # recent and analysed   -> kept
            s.add_all(rows); s.commit()
            created = [r.id for r in rows]

        print("--- age rule")
        with Session(engine) as s:
            out = prune_raw_csi(s, retention_hours=24, max_rows=0, now=now)
            left = {r.id: r for r in s.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.id.in_(created))).all()}
        assert len(left) == 10, f"expected 10 of 12 test packets left, got {len(left)}"
        assert sum(1 for r in left.values() if r.event_id is None) == 4, "unprocessed packets must survive the age rule"
        assert sum(1 for r in left.values() if r.event_id == ev_id) == 6
        assert out["deleted_by_age"] >= 8
        print("[PASS] analysed/skipped packets past the window are deleted; unprocessed and recent ones stay")

        print("--- detection results are untouched")
        with Session(engine) as s:
            assert s.get(SensingEvent, ev_id) is not None
        print("[PASS] the detection event still exists")

        print("--- row cap")
        with Session(engine) as s:
            total = retention_status(s)["raw_packets_stored"]
            out = prune_raw_csi(s, retention_hours=0, max_rows=total - 3, now=now)
            after = retention_status(s)["raw_packets_stored"]
            pending_left = s.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.id.in_(created), RawCsiTelemetry.event_id.is_(None))).all()
        assert out["deleted_by_cap"] == 3 and after == total - 3, (out, total, after)
        assert len(pending_left) == 4, "the cap must not drop unprocessed packets"
        print("[PASS] the oldest analysed packets go first when the table passes its cap")

        print("--- unprocessed packets are never dropped silently")
        with Session(engine) as s:
            pending_total = s.exec(select(RawCsiTelemetry.id).where(RawCsiTelemetry.event_id.is_(None))).all()
            out = prune_raw_csi(s, retention_hours=0, max_rows=1, now=now)
            still = s.exec(select(RawCsiTelemetry.id).where(RawCsiTelemetry.event_id.is_(None))).all()
            status = retention_status(s, max_rows=1)
        assert len(still) == len(pending_total), "unprocessed packets were deleted"
        assert status["over_cap_with_nothing_deletable"] is True
        print("[PASS] over the cap with only unprocessed packets: nothing is dropped, and the status says so")

        print("--- /sensing/retention")
        st, body = call("/sensing/retention", token=fm)
        assert st == 200 and body["policy"]["unprocessed_packets_are_never_age_deleted"] is True and "raw_packets_stored" in body, body
        st, _ = call("/sensing/retention", token=care)
        assert st == 403, "caregivers must not read the retention policy"
        print("[PASS] managers can read the policy; caregivers get 403")
        print("\nALL RAW CSI RETENTION TESTS PASSED")
    finally:
        with Session(engine) as s:
            for r in s.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == device_id)).all():
                s.delete(r)
            s.commit()
            for e in s.exec(select(SensingEvent).where(SensingEvent.device_id == device_id)).all():
                s.delete(e)
            s.commit()
            d = s.get(SensingDevice, device_id)
            if d:
                s.delete(d)
            s.commit()


if __name__ == "__main__":
    run()
