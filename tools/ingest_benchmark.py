"""
Measure how fast and how consistently POST /sensing/ingest accepts packets, for a registered device.

  python tools/ingest_benchmark.py --api http://127.0.0.1:8000 --token TK-... --batches 60 --batch-size 50 --format b64 --keepalive

It sends synthetic packets, so use a device registered with allowed_source "simulated" (they are stored as DEMO data,
never mixed with hardware). It reports the client-observed round trip, the server-reported processing time
(X-Process-Ms) and the effective packets per second, which is the number to compare with the radio's ~100 packets/s.
Run it once per setting (--format list|b64, --keepalive or not, --batch-size) to see what each change buys.
"""
import argparse
import base64
import http.client
import json
import random
import statistics
import time
import urllib.parse


def make_packet(seq, fmt):
    iq = [random.randint(-40, 40) for _ in range(104)]
    csi = {"src_mac": "24:0a:c4:00:00:01"}
    if fmt == "b64":
        csi["iq_b64"] = base64.b64encode(bytes(v & 0xFF for v in iq)).decode()
    else:
        csi["iq"] = iq
    return {"sequence_number": seq, "rssi": -55, "noise_floor": -92, "channel": 6, "bandwidth_mhz": 20,
            "subcarrier_count": 52, "provenance": "simulated", "csi_data": csi,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + ".%03dZ" % (int(time.time() * 1000) % 1000)}


def pct(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(round(q * (len(v) - 1))))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    ap.add_argument("--batches", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("--format", choices=["list", "b64"], default="b64")
    ap.add_argument("--keepalive", action="store_true", help="reuse one connection (what the bridge does)")
    a = ap.parse_args()
    u = urllib.parse.urlparse(a.api)
    Conn = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = Conn(u.netloc, timeout=30) if a.keepalive else None
    rtts, servers, sizes = [], [], []
    seq = 0
    t_all = time.perf_counter()
    for _ in range(a.batches):
        body = json.dumps({"packets": [make_packet(seq + i, a.format) for i in range(a.batch_size)]}).encode()
        seq += a.batch_size
        sizes.append(len(body))
        c = conn or Conn(u.netloc, timeout=30)
        t0 = time.perf_counter()
        c.request("POST", "/sensing/ingest", body, {"Content-Type": "application/json", "X-Device-Token": a.token,
                                                    "X-Client-Rtt-Ms": "%.1f" % (rtts[-1] if rtts else 0)})
        r = c.getresponse()
        r.read()
        rtts.append((time.perf_counter() - t0) * 1000)
        if r.status != 201:
            raise SystemExit(f"HTTP {r.status}: {r.read()[:200]!r}")
        servers.append(float(r.getheader("X-Process-Ms") or 0))
        if not conn:
            c.close()
    total = time.perf_counter() - t_all
    n = a.batches * a.batch_size
    print(f"format={a.format} keepalive={a.keepalive} batch={a.batch_size} request_bytes~{int(statistics.mean(sizes))}")
    print(f"round trip ms   p50={pct(rtts, .5):.1f} p95={pct(rtts, .95):.1f}")
    print(f"server ms       p50={pct(servers, .5):.1f} p95={pct(servers, .95):.1f}")
    print(f"throughput      {n / total:.0f} packets/s sustained by one sender ({n} packets in {total:.1f}s)")


if __name__ == "__main__":
    main()
