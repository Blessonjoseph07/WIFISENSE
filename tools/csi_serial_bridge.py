"""
Serial -> API bridge for the ESP32-S3 CSI receiver (firmware/csi_recv).

The receiver prints one line per CSI packet on USB serial. This tool reads them, checks them, and POSTs batches to
POST /sensing/ingest with the device token, exactly in the format docs/firmware_contract.md describes.

  python tools/csi_serial_bridge.py --port COM4 --token TK-ESP32-... --api http://127.0.0.1:8000
  python tools/csi_serial_bridge.py --file capture.txt --dry-run          # parse and verify only, nothing is sent

Safety rules (nothing here invents or labels data)
  * Only lines the firmware itself printed are used. Anything that is not exactly 104 integers in int8 range, or whose
    radio format is not non-HT 20 MHz, is counted and dropped, never repaired.
  * Every ~256th packet the firmware also prints the raw 128-value buffer (CSI_RAW). The bridge converts it with the
    reference implementation (tools/csi_buffer_to_iq.py) and compares it with the firmware's own conversion. On any
    mismatch it stops sending and says so: the firmware's byte order is wrong.
  * No activity labels are ever added. A wrong token (401/403) stops the bridge; the registered device decides whether the
    packets are LIVE (the API rejects a different provenance).

Needs pyserial for --port (pip install pyserial). --file needs nothing extra.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csi_buffer_to_iq import convert as reference_convert  # noqa: E402

N_IQ = 104
MAC_RE = re.compile(r"^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$")


def parse_iq_line(line: str) -> Optional[Dict]:
    """CSI_IQ,seq,mac,rssi,rate,sig_mode,mcs,cwb,noise_floor,channel,first_word_invalid,[i0,q0,...]  -> dict or None."""
    if not line.startswith("CSI_IQ,"):
        return None
    head, sep, tail = line.strip().partition(",[")
    if not sep or not tail.endswith("]"):
        return None
    f = head.split(",")
    if len(f) != 11:          # type,seq,mac,rssi,rate,sig_mode,mcs,cwb,noise_floor,channel,first_word_invalid
        return None
    try:
        iq = [int(v) for v in tail[:-1].split(",")]
        out = {"seq": int(f[1]), "mac": f[2].lower(), "rssi": int(f[3]), "rate": int(f[4]), "sig_mode": int(f[5]),
               "mcs": int(f[6]), "cwb": int(f[7]), "noise": int(f[8]), "channel": int(f[9]), "iq": iq}
    except ValueError:
        return None
    if not MAC_RE.match(out["mac"]) or len(iq) != N_IQ or any(not -128 <= v <= 127 for v in iq):
        return None
    if out["sig_mode"] != 0 or out["cwb"] != 0:
        return None
    if not (-120 <= out["rssi"] <= 0) or not (1 <= out["channel"] <= 14):
        return None
    return out


def parse_raw_line(line: str) -> Optional[Dict]:
    """CSI_RAW,seq,[v0,...,v127]"""
    if not line.startswith("CSI_RAW,"):
        return None
    head, sep, tail = line.strip().partition(",[")
    if not sep or not tail.endswith("]"):
        return None
    try:
        return {"seq": int(head.split(",")[1]), "buf": [int(v) for v in tail[:-1].split(",")]}
    except (ValueError, IndexError):
        return None


def to_packet(p: Dict, provenance: str) -> Dict:
    return {
        "sequence_number": p["seq"] & 0x7FFFFFFF,
        "rssi": p["rssi"],
        "noise_floor": p["noise"] if -120 <= p["noise"] <= 0 else None,
        "subcarrier_count": 52,
        "bandwidth_mhz": 20,
        "channel": p["channel"],
        "provenance": provenance,
        "csi_data": {"iq": p["iq"], "src_mac": p["mac"], "rate": p["rate"], "sig_mode": p["sig_mode"], "mcs": p["mcs"], "cwb": p["cwb"]},
    }


class Poster:
    def __init__(self, api: str, token: str, dry_run: bool):
        self.url, self.token, self.dry = api.rstrip("/") + "/sensing/ingest", token, dry_run
        self.sent = self.http_errors = 0
        self.last_status: Optional[int] = None

    def post(self, packets: List[Dict]) -> None:
        if self.dry or not packets:
            self.sent += len(packets)
            return
        req = urllib.request.Request(self.url, data=json.dumps({"packets": packets}).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "X-Device-Token": self.token})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                self.last_status = r.status
                self.sent += len(packets)
        except urllib.error.HTTPError as e:
            self.last_status = e.code
            self.http_errors += 1
            body = e.read().decode(errors="replace")[:300]
            if e.code in (401, 403):
                sys.exit(f"\nSTOPPED: the API rejected the device token ({e.code}): {body}")
            print(f"\nHTTP {e.code} from the API: {body}", flush=True)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            self.http_errors += 1
            self.last_status = None
            print(f"\ncannot reach the API ({e}); batch dropped", flush=True)


def lines_from(args):
    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                yield ln
        return
    try:
        import serial  # type: ignore
    except ImportError:
        sys.exit("pyserial is not installed: pip install pyserial")
    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        buf = b""
        while True:
            chunk = ser.read(4096)
            if not chunk:
                yield ""        # lets the caller flush on idle
                continue
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                yield raw.decode(errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--port", help="serial port, e.g. COM4")
    src.add_argument("--file", help="a saved serial capture (for testing)")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--token", default=os.getenv("WIFISENSE_DEVICE_TOKEN", ""))
    ap.add_argument("--tx-mac", default="1a:00:00:00:00:00", help="only packets from this transmitter are used")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--provenance", default="live", choices=["live", "simulated", "dataset"],
                    help="must match the registered device; 'live' for real hardware")
    ap.add_argument("--dry-run", action="store_true", help="parse and verify, send nothing")
    a = ap.parse_args()
    if not a.dry_run and not a.token:
        ap.error("--token (or WIFISENSE_DEVICE_TOKEN) is required unless --dry-run")

    poster = Poster(a.api, a.token, a.dry_run)
    batch: List[Dict] = []
    last_iq: Dict[int, List[int]] = {}
    read = dropped = raw_ok = 0
    mismatch = False
    t_start = t_flush = t_report = time.time()
    try:
        for line in lines_from(a):
            now = time.time()
            p = parse_iq_line(line) if line else None
            if line.startswith("CSI_IQ,"):
                if p is None or p["mac"] != a.tx_mac.lower():
                    dropped += 1
                else:
                    read += 1
                    last_iq = {p["seq"]: p["iq"]}
                    batch.append(to_packet(p, a.provenance))
            elif line.startswith("CSI_RAW,"):
                raw = parse_raw_line(line)
                try:
                    ref = reference_convert(raw["buf"]) if raw else None
                except ValueError as exc:
                    sys.exit(f"STOPPED: the raw CSI buffer is not the supported layout: {exc}")
                if raw and raw["seq"] in last_iq:
                    if ref != last_iq[raw["seq"]]:
                        mismatch = True
                        sys.exit("STOPPED: the firmware's I/Q conversion DISAGREES with the reference conversion for the same packet. "
                                 "The byte order or slot order in firmware/csi_recv is wrong. Nothing more was sent.")
                    raw_ok += 1
            if len(batch) >= a.batch or (batch and now - t_flush > 0.5):
                poster.post(batch)
                batch, t_flush = [], now
            if now - t_report >= 2:
                span = max(now - t_start, 1e-6)
                print(f"\rread={read} ({read / span:.0f}/s) sent={poster.sent} dropped_format={dropped} "
                      f"raw_checks_ok={raw_ok} http_errors={poster.http_errors} last_http={poster.last_status}", end="", flush=True)
                t_report = now
    except KeyboardInterrupt:
        pass
    if batch and not mismatch:
        poster.post(batch)
    print(f"\nfinished: read={read} sent={poster.sent} dropped_format={dropped} raw_checks_ok={raw_ok} http_errors={poster.http_errors}"
          + (" (dry run: nothing sent)" if a.dry_run else ""))


if __name__ == "__main__":
    main()
