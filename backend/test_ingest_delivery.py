"""
INGEST DELIVERY TEST SUITE
==========================
The fast, reported path from a device to the cloud:
  * csi_data.iq_b64 (compact base64 int8) is accepted, expanded to the same stored `iq` list, and bad input is rejected
  * every ingest response carries server_ms and an X-Process-Ms header
  * the bridge's store-and-forward sender (tools/csi_serial_bridge.Poster) batches, retries a failing server in order
    without losing or reordering packets, reports overflow instead of dropping silently, and stops on a 401
  * delivery metrics (server time, ingest delay, the bridge's own round trip and queue depth) appear in /devices/{id}/live
Runs against API_BASE (a seeded server) and DATABASE_URL.
"""
import base64
import http.server
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import csi_serial_bridge as bridge  # noqa: E402

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def call(path, method="GET", data=None, token=None, headers=None, raw=False):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    h.update(headers or {})
    req = urllib.request.Request(API_BASE + path, data=json.dumps(data).encode() if data is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            body = json.loads(r.read() or b"null")
            return (r.status, body, dict(r.headers)) if raw else (r.status, body)
    except urllib.error.HTTPError as e:
        body = json.loads(e.read() or b"null")
        return (e.code, body, dict(e.headers)) if raw else (e.code, body)


def login(email, password):
    st, body = call("/auth/login", "POST", {"email": email, "password": password})
    assert st == 200, body
    return body["access_token"]


def packet(seq, iq=None, rng=None, compact=False):
    iq = iq if iq is not None else [int(v) for v in np.clip(np.round(rng.normal(0, 30, 104)), -127, 127)]
    csi = {"src_mac": "24:0A:C4:00:00:01"}
    if compact:
        csi["iq_b64"] = base64.b64encode(bytes(v & 0xFF for v in iq)).decode()
    else:
        csi["iq"] = iq
    return {"sequence_number": seq, "rssi": -55, "noise_floor": -92, "channel": 6, "bandwidth_mhz": 20,
            "subcarrier_count": 52, "provenance": "simulated", "csi_data": csi}


class FakeIngest(http.server.BaseHTTPRequestHandler):
    """Stands in for the API: fails the first `fail_first` requests with `fail_code`, then accepts and records."""
    fail_first, fail_code, received, hits, headers_seen = 0, 503, [], 0, []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        cls = type(self)
        cls.hits += 1
        cls.headers_seen.append(dict(self.headers))
        if cls.hits <= cls.fail_first:
            self.send_response(cls.fail_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"try again"}')
            return
        cls.received.extend(json.loads(body)["packets"])
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Process-Ms", "3.5")
        self.end_headers()
        self.wfile.write(b'{"status":"success"}')

    def log_message(self, *a):
        pass


def fake_server(fail_first=0, fail_code=503):
    handler = type("H", (FakeIngest,), {"fail_first": fail_first, "fail_code": fail_code, "received": [], "hits": 0, "headers_seen": []})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, handler, f"http://127.0.0.1:{srv.server_address[1]}"


def wait_for(cond, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


def wire_packet(seq):
    """A bridge-style packet (iq list); Poster converts it for the wire."""
    return {"sequence_number": seq, "rssi": -55, "subcarrier_count": 52, "bandwidth_mhz": 20, "channel": 6, "provenance": "simulated",
            "csi_data": {"iq": [seq % 100 - 50] * 104, "src_mac": "24:0a:c4:00:00:01"}}


def run():
    fm = login("elizabeth@wifisense.com", "elizabethpassword")
    rooms = call("/rooms", token=fm)[1]
    room = [r for r in rooms if "101" in r["name"]][0]
    mac = "24:0A:C4:%02X:%02X:%02X" % tuple(uuid.uuid4().bytes[:3])
    st, dev = call("/devices", "POST", {"room_id": room["id"], "mac_address": mac, "device_status": "ONLINE",
                                        "firmware_version": "test", "allowed_source": "simulated"}, fm)
    assert st == 201, dev
    did, tok = dev["id"], dev["hardware_token"]
    rng = np.random.default_rng(3)

    print("--- compact iq_b64 format")
    iq = [int(v) for v in np.clip(np.round(rng.normal(0, 60, 104)), -128, 127)]
    iq[0], iq[1] = -128, 127          # extremes survive the unsigned-byte round trip
    st, body, hdr = call("/sensing/ingest", "POST", {"packets": [packet(1, iq=iq, compact=True)]}, headers={"X-Device-Token": tok}, raw=True)
    assert st == 201 and body["ingested_count"] == 1, body
    st, live = call(f"/sensing/devices/{did}/live", token=fm)
    assert st == 200 and live["packets"][-1]["seq"] == 1, live
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.entities import RawCsiTelemetry
    with Session(engine) as s:
        stored = s.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == did, RawCsiTelemetry.sequence_number == 1)).first()
    assert stored.csi_data["iq"] == iq and "iq_b64" not in stored.csi_data, "iq_b64 must be stored as the ordinary iq list"
    print("[PASS] iq_b64 is expanded and stored exactly like iq (including -128 and 127)")

    st, bad = call("/sensing/ingest", "POST", {"packets": [{**packet(2, rng=rng), "csi_data": {"iq": iq, "iq_b64": "AAAA"}}]}, headers={"X-Device-Token": tok})
    assert st == 422, (st, bad)
    st, bad = call("/sensing/ingest", "POST", {"packets": [{**packet(3, rng=rng), "csi_data": {"iq_b64": "not base64 !!"}}]}, headers={"X-Device-Token": tok})
    assert st == 422, (st, bad)
    st, bad = call("/sensing/ingest", "POST", {"packets": [{**packet(4, rng=rng), "csi_data": {"iq_b64": base64.b64encode(bytes(600)).decode()}}]}, headers={"X-Device-Token": tok})
    assert st == 422, (st, bad)
    print("[PASS] both formats at once, invalid base64 and an oversized payload are rejected (422)")

    print("--- the server reports its own time")
    assert "X-Process-Ms" in hdr or "x-process-ms" in {k.lower() for k in hdr}, hdr
    assert body["server_ms"] is not None and body["server_ms"] >= 0
    print(f"[PASS] server_ms={body['server_ms']} and X-Process-Ms header present")

    print("--- store-and-forward sender: retries in order, loses nothing")
    srv, handler, url = fake_server(fail_first=2, fail_code=503)
    p = bridge.Poster(url, "TK-test", dry_run=False, wire="b64", batch_max=20, max_wait=0.05)
    for i in range(55):
        p.submit(wire_packet(i))
    assert wait_for(lambda: len(handler.received) == 55), (len(handler.received), p.retries, p.http_errors)
    p.close()
    seqs = [x["sequence_number"] for x in handler.received]
    assert seqs == list(range(55)), "packets must arrive complete and in order after retries"
    assert p.retries >= 2 and p.sent == 55 and p.dropped_overflow == 0, (p.retries, p.sent)
    assert all("iq_b64" in x["csi_data"] and "iq" not in x["csi_data"] for x in handler.received), "b64 wire format expected"
    assert any("X-Client-Queue" in h or "x-client-queue" in {k.lower() for k in h} for h in handler.headers_seen)
    srv.shutdown()
    print(f"[PASS] 55 packets delivered in order after {p.retries} retries; the b64 wire format and X-Client-* headers were used")

    print("--- overflow is reported, never silent")
    srv, handler, url = fake_server(fail_first=10 ** 6, fail_code=503)
    p = bridge.Poster(url, "TK-test", dry_run=False, batch_max=100, max_wait=3.0, max_queue=5)
    for i in range(12):
        p.submit(wire_packet(i))
    assert p.dropped_overflow == 7 and p.queued == 5, (p.dropped_overflow, p.queued)
    p.fatal = "test over"          # lets the sender thread stop
    srv.shutdown()
    print("[PASS] with a full queue the oldest packets are dropped and counted (7 of 12)")

    print("--- a rejected token stops the sender")
    srv, handler, url = fake_server(fail_first=10 ** 6, fail_code=401)
    p = bridge.Poster(url, "TK-wrong", dry_run=False, batch_max=5, max_wait=0.05)
    for i in range(5):
        p.submit(wire_packet(i))
    assert wait_for(lambda: p.fatal is not None), "401 must stop the bridge"
    assert handler.hits == 1, f"a 401 must not be retried (hits={handler.hits})"
    srv.shutdown()
    print("[PASS] 401 sets a fatal error after one request")

    print("--- delivery metrics in the live endpoint")
    now = time.time()
    from datetime import datetime, timezone, timedelta
    ts = (datetime.now(timezone.utc) - timedelta(milliseconds=180)).isoformat()
    pk = packet(100, rng=rng, compact=True)
    pk["timestamp"] = ts
    st, body = call("/sensing/ingest", "POST", {"packets": [pk]}, headers={"X-Device-Token": tok, "X-Client-Rtt-Ms": "42.5", "X-Client-Queue": "7"})
    assert st == 201, body
    st, live = call(f"/sensing/devices/{did}/live", token=fm)
    d = live["delivery"]
    assert d["batches"] >= 2 and d["server_ms"]["p50"] is not None, d
    assert d["ingest_delay_ms"] and d["ingest_delay_ms"]["p95"] >= 150, d
    assert d["client_rtt_ms"]["p50"] == 42.5 and d["bridge_queue_depth"] == 7, d
    print(f"[PASS] delivery: server p50 {d['server_ms']['p50']} ms, ingest delay p95 {d['ingest_delay_ms']['p95']} ms, bridge rtt 42.5 ms, queue 7")

    print("\nALL INGEST DELIVERY TESTS PASSED")
    with Session(engine) as s:
        for r in s.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == did)).all():
            s.delete(r)
        s.commit()
        from app.models.entities import SensingDevice
        d_ = s.get(SensingDevice, did)
        if d_:
            s.delete(d_)
        s.commit()


if __name__ == "__main__":
    run()
