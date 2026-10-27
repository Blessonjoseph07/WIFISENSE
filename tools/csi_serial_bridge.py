"""
Serial -> API bridge for the ESP32-S3 CSI receiver (firmware/csi_recv).

The receiver prints one line per CSI packet on USB serial. This tool reads them, checks them, and POSTs batches to
POST /sensing/ingest with the device token, exactly in the format docs/firmware_contract.md describes.

  python tools/csi_serial_bridge.py --port COM4 --token TK-ESP32-... --api http://127.0.0.1:8000
  python tools/csi_serial_bridge.py --file capture.txt --dry-run          # parse and verify only, nothing is sent

Board display: with --port (and not --dry-run) the bridge also asks the API every 2 s what this device may show
(GET /sensing/device/state, same device token) and writes one line back to the receiver, which shows it on its OLED:
  WS_STATE,<presence text>,<room state text>

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
import base64
import collections
import http.client
import json
import os
import re
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csi_buffer_to_iq import convert as reference_convert  # noqa: E402

N_IQ = 104
MAC_RE = re.compile(r"^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$")


def hex_to_int8(h: str) -> Optional[List[int]]:
    """'ff01...' (two hex digits per int8, two's complement) -> list of ints, or None if malformed."""
    if len(h) % 2 or not re.fullmatch(r"[0-9a-fA-F]*", h):
        return None
    return [b - 256 if b > 127 else b for b in bytes.fromhex(h)]


def parse_iq_line(line: str) -> Optional[Dict]:
    """CSI_IQ,seq,mac,rssi,rate,sig_mode,mcs,cwb,noise_floor,channel,first_word_invalid,<208 hex digits>  -> dict or None."""
    if not line.startswith("CSI_IQ,"):
        return None
    f = line.strip().split(",")
    if len(f) != 12:          # type,seq,mac,rssi,rate,sig_mode,mcs,cwb,noise_floor,channel,first_word_invalid,iq_hex
        return None
    try:
        iq = hex_to_int8(f[11])
        if iq is None:
            return None
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
    """CSI_RAW,seq,<256 hex digits>"""
    if not line.startswith("CSI_RAW,"):
        return None
    f = line.strip().split(",")
    if len(f) != 3:
        return None
    try:
        buf = hex_to_int8(f[2])
        return {"seq": int(f[1]), "buf": buf} if buf is not None else None
    except ValueError:
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


def compact(packet: Dict) -> Dict:
    """Wire form with the I/Q values base64-encoded (about half the bytes of the integer list); the API expands it again."""
    csi = dict(packet["csi_data"])
    csi["iq_b64"] = base64.b64encode(bytes(v & 0xFF for v in csi.pop("iq"))).decode()
    return {**packet, "csi_data": csi}


class _HttpError(Exception):
    def __init__(self, code: int, body: str):
        super().__init__(f"HTTP {code}")
        self.code, self.body = code, body


class Poster:
    """Store-and-forward sender. The serial reader only calls submit(); a background thread batches packets and posts them
    over ONE persistent connection, so a slow or briefly unreachable network never stalls the serial port.

      * batches go out when `batch_max` packets are waiting or `max_wait` seconds have passed since the first one
      * a failed batch (network error, 5xx, 429) is retried in order with exponential backoff, never skipped
      * the queue is bounded: when it is full the OLDEST packets are dropped and counted (reported, never silent)
      * a 401/403 stops everything; other 4xx batches are dropped and counted, since retrying cannot fix them
      * each request tells the server the previous round trip time and the current queue depth (X-Client-* headers)
    """

    def __init__(self, api: str, token: str, dry_run: bool, wire: str = "b64", batch_max: int = 50,
                 max_wait: float = 0.25, max_queue: int = 20000):
        self.api, self.token, self.dry, self.wire = api.rstrip("/"), token, dry_run, wire
        self.batch_max, self.max_wait, self.max_queue = batch_max, max_wait, max_queue
        u = urllib.parse.urlparse(self.api)
        self._https, self._host, self._prefix = u.scheme == "https", u.netloc, u.path.rstrip("/")
        self.sent = self.http_errors = self.retries = self.dropped_overflow = self.dropped_rejected = 0
        self.last_status: Optional[int] = None
        self.fatal: Optional[str] = None
        self.rtts: Deque[float] = collections.deque(maxlen=200)
        self.server_ms: Deque[float] = collections.deque(maxlen=200)
        self._q: Deque[Dict] = collections.deque()
        self._cv = threading.Condition()
        self._closing = False
        self._conn = None
        self._thread: Optional[threading.Thread] = None

    # -- producer side ------------------------------------------------------------------------------------------
    def submit(self, packet: Dict) -> None:
        if self.dry:
            self.sent += 1
            return
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="csi-sender", daemon=True)
            self._thread.start()
        with self._cv:
            if len(self._q) >= self.max_queue:
                self._q.popleft()
                self.dropped_overflow += 1
            self._q.append(packet)
            self._cv.notify()

    @property
    def queued(self) -> int:
        return len(self._q)

    def close(self, timeout: float = 15.0) -> None:
        """Send what is still queued (up to `timeout` seconds), then stop."""
        if self._thread is None:
            return
        with self._cv:
            self._closing = True
            self._cv.notify_all()
        self._thread.join(timeout)

    # -- sender thread --------------------------------------------------------------------------------------------
    def _next_batch(self) -> List[Dict]:
        with self._cv:
            while not self._q and not self._closing and not self.fatal:
                self._cv.wait(0.5)
            if not self._q:
                return []
            first = time.time()
            while len(self._q) < self.batch_max and not self._closing:
                left = self.max_wait - (time.time() - first)
                if left <= 0:
                    break
                self._cv.wait(left)
            n = min(self.batch_max, len(self._q))
            return [self._q.popleft() for _ in range(n)]

    def _connection(self):
        if self._conn is None:
            cls = http.client.HTTPSConnection if self._https else http.client.HTTPConnection
            self._conn = cls(self._host, timeout=10)
        return self._conn

    def _post_once(self, packets: List[Dict]) -> int:
        wire = [compact(p) for p in packets] if self.wire == "b64" else packets
        body = json.dumps({"packets": wire}).encode()
        headers = {"Content-Type": "application/json", "X-Device-Token": self.token,
                   "X-Client-Queue": str(self.queued), "X-Client-Dropped": str(self.dropped_overflow)}
        if self.rtts:
            headers["X-Client-Rtt-Ms"] = "%.1f" % self.rtts[-1]
        t0 = time.perf_counter()
        conn = self._connection()
        conn.request("POST", self._prefix + "/sensing/ingest", body, headers)
        resp = conn.getresponse()
        data = resp.read()
        self.rtts.append((time.perf_counter() - t0) * 1000)
        try:
            self.server_ms.append(float(resp.getheader("X-Process-Ms") or 0))
        except ValueError:
            pass
        self.last_status = resp.status
        if resp.status >= 400:
            raise _HttpError(resp.status, data.decode(errors="replace")[:300])
        return resp.status

    def _run(self) -> None:
        while True:
            batch = self._next_batch()
            if not batch:
                if self._closing or self.fatal:
                    return
                continue
            delay = 0.5
            while True:
                try:
                    self._post_once(batch)
                    self.sent += len(batch)
                    break
                except _HttpError as e:
                    self.http_errors += 1
                    if e.code in (401, 403):
                        self.fatal = f"the API rejected the device token ({e.code}): {e.body}"
                        return
                    hint = provenance_hint(e.body) if e.code == 400 else None
                    if hint:                                   # every batch would be refused the same way: stop now
                        self.fatal = hint
                        return
                    if not (e.code == 429 or e.code >= 500):
                        self.dropped_rejected += len(batch)
                        print(f"\nHTTP {e.code} from the API, batch of {len(batch)} dropped: {e.body}", flush=True)
                        break
                except (OSError, http.client.HTTPException):
                    self.http_errors += 1
                except Exception as exc:                      # anything else would kill this thread silently
                    self.fatal = f"the sender stopped: {type(exc).__name__}: {exc}"
                    return
                if self._conn is not None:
                    try:
                        self._conn.close()
                    except OSError:
                        pass
                    self._conn = None
                self.retries += 1
                if self._closing and delay >= 4:   # shutting down and the network is still down: stop waiting
                    self.dropped_rejected += len(batch)
                    break
                time.sleep(delay)
                delay = min(delay * 2, 8)

    # -- reporting ------------------------------------------------------------------------------------------------
    def latency(self) -> str:
        if not self.rtts:
            return "rtt=-"
        r = sorted(self.rtts)
        s = sorted(self.server_ms) if self.server_ms else [0.0]
        return (f"rtt p50={r[len(r) // 2]:.0f} p95={r[min(len(r) - 1, int(len(r) * 0.95))]:.0f}ms "
                f"server p50={s[len(s) // 2]:.0f}ms")


def clean_token(raw: Optional[str]) -> str:
    """The token as typed or pasted, without what copying from a web page or an example adds: spaces and line breaks
    anywhere (a token never contains them), surrounding quotes, and the <...> of a 'put your token here' example."""
    t = re.sub(r"\s+", "", raw or "")
    return t.strip("\"'").strip("<>").strip("\"'")


def provenance_hint(body: str) -> Optional[str]:
    """A plain explanation when the API refuses packets because the token belongs to another kind of device."""
    m = re.search(r"device is restricted to '(\w+)'", body or "")
    if not m:
        return None
    kind = {"dataset": "DATASET REPLAY", "simulated": "DEMO", "live": "LIVE HARDWARE"}.get(m.group(1), m.group(1))
    return (f"this token belongs to a {kind} device, not to the live receiver. On Devices & Service Desk press RESET "
            "TOKEN on the receiver's own row (its MAC, data source Live hardware) and start the bridge with that token.")


ROOM_SHORT = {"empty": "EMPTY", "still": "STILL", "walking": "WALKING", "few": "FEW PEOPLE", "busy": "BUSY", "moving": "MOVING",
              "presence": "PRESENCE"}
PRESENCE_SHORT = {"MOVEMENT": "PRESENCE+MOVE", "PRESENT": "PRESENCE", "QUIET": "NO PRESENCE", "STALE": "NOT SENDING", "NO_DATA": "NO DATA"}


def display_lines(state: Dict) -> str:
    """The WS_STATE line for the receiver's OLED (ASCII, no commas, each part at most 16 characters). A learned room state the
    API marked not reliable gets a '?' so the display never looks more certain than the model is."""
    if state.get("paused"):
        return "WS_STATE,PAUSED,RESUME ON SITE\n"
    top = PRESENCE_SHORT.get(state.get("movement_state"), "NO DATA")
    room = state.get("room_state")
    if room and room.get("confidence") is None:      # from the movement check, not the model: no percentage to show
        bottom = ROOM_SHORT.get(room.get("label"), "UNKNOWN")
    elif room:
        bottom = f"{ROOM_SHORT.get(room.get('label'), 'UNKNOWN')} {round(100 * float(room.get('confidence') or 0))}%"
        if not room.get("reliable"):
            bottom += "?"
    else:
        bottom = "NOT TRAINED"
    clean = lambda t: re.sub(r"[^ -~]", "", t).replace(",", " ")[:16]
    return f"WS_STATE,{clean(top)},{clean(bottom)}\n"


class StateRelay:
    """Every `period` seconds: GET /sensing/device/state with the device token and write display_lines() to the serial port.
    Best effort: a failed request just skips that update (the board keeps showing its own radio statistics)."""

    def __init__(self, api: str, token: str, period: float = 2.0):
        u = urllib.parse.urlparse(api)
        self._https, self._host, self._prefix = u.scheme == "https", u.netloc, u.path.rstrip("/")
        self.token, self.period, self.ser, self.updates, self.errors = token, period, None, 0, 0
        self.paused = False   # an operator pressed Pause on the website: forward nothing until Resume
        threading.Thread(target=self._run, name="state-relay", daemon=True).start()

    def _run(self) -> None:
        conn = None
        while True:
            time.sleep(self.period)
            if self.ser is None:
                continue
            try:
                if conn is None:
                    conn = (http.client.HTTPSConnection if self._https else http.client.HTTPConnection)(self._host, timeout=10)
                conn.request("GET", self._prefix + "/sensing/device/state", headers={"X-Device-Token": self.token})
                resp = conn.getresponse()
                data = resp.read()
                if resp.status != 200:
                    raise OSError(f"HTTP {resp.status}")
                state = json.loads(data)
                self.paused = bool(state.get("paused"))
                self.ser.write(display_lines(state).encode("ascii"))
                self.updates += 1
            except Exception:
                self.errors += 1
                if conn is not None:
                    conn.close()
                    conn = None


def lines_from(args, relay=None):
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
        if relay is not None:
            relay.ser = ser
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
    ap.add_argument("--batch", type=int, default=50, help="send when this many packets are waiting (the API accepts up to 100)")
    ap.add_argument("--max-wait-ms", type=int, default=250, help="...or when the oldest waiting packet is this old")
    ap.add_argument("--max-queue", type=int, default=1000,
                    help="packets kept while the API is slow; older ones are dropped so the view stays live (default 1000)")
    ap.add_argument("--every", type=int, default=1,
                    help="forward only every Nth packet (e.g. 3 for the free hosted API: ~30/s instead of ~90/s). Record the "
                         "baseline and the training at the same setting you run with.")
    ap.add_argument("--wire", choices=["b64", "list"], default="b64",
                    help="I/Q encoding on the wire: b64 (compact, needs this repo's API) or list (plain integers)")
    ap.add_argument("--provenance", default="live", choices=["live", "simulated", "dataset"],
                    help="must match the registered device; 'live' for real hardware")
    ap.add_argument("--dry-run", action="store_true", help="parse and verify, send nothing")
    a = ap.parse_args()
    a.token = clean_token(a.token)
    if not a.dry_run and not a.token:
        ap.error("--token (or WIFISENSE_DEVICE_TOKEN) is required unless --dry-run")
    if a.token and not re.fullmatch(r"[A-Za-z0-9_\-]+", a.token):
        ap.error("the device token contains characters a token never has (spaces or symbols). Copy it again from "
                 "Devices & Service Desk > RESET TOKEN and pass it as --token \"TK-ESP32-...\" on one line.")
    if a.every < 1:
        ap.error("--every must be 1 or more")

    poster = Poster(a.api, a.token, a.dry_run, wire=a.wire, batch_max=max(1, min(a.batch, 100)), max_wait=a.max_wait_ms / 1000,
                    max_queue=a.max_queue)
    paused_skipped = 0
    relay = StateRelay(a.api, a.token) if (a.port and not a.dry_run) else None
    last_iq: Dict[int, List[int]] = {}
    read = dropped = raw_ok = 0
    mismatch = False
    t_start = t_report = time.time()
    try:
        for line in lines_from(a, relay):
            now = time.time()
            p = parse_iq_line(line) if line else None
            if line.startswith("CSI_IQ,"):
                if p is None or p["mac"] != a.tx_mac.lower():
                    dropped += 1
                else:
                    read += 1
                    last_iq = {p["seq"]: p["iq"]}
                    pkt = to_packet(p, a.provenance)
                    # when the bridge read it: lets the API measure how long delivery took (ingest delay)
                    pkt["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
                    if relay is not None and relay.paused:
                        paused_skipped += 1                   # paused on the website: measure nothing
                    elif (read - 1) % a.every == 0:          # --every N: forward 1 packet in N (a slow hosted API)
                        poster.submit(pkt)
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
            if poster.fatal:
                sys.exit(f"\nSTOPPED: {poster.fatal}")
            if now - t_report >= 2:
                span = max(now - t_start, 1e-6)
                print(f"\r{'PAUSED (Resume on the website) ' if relay is not None and relay.paused else ''}"
                      f"read={read} ({read / span:.0f}/s) sent={poster.sent} queued={poster.queued} dropped_format={dropped} "
                      f"raw_checks_ok={raw_ok} http_errors={poster.http_errors} retries={poster.retries} "
                      f"overflow_dropped={poster.dropped_overflow} last_http={poster.last_status} {poster.latency()}   ", end="", flush=True)
                t_report = now
    except KeyboardInterrupt:
        pass
    if not mismatch:
        poster.close()
    print(f"\nfinished: read={read} sent={poster.sent} dropped_format={dropped} raw_checks_ok={raw_ok} http_errors={poster.http_errors} "
          f"retries={poster.retries} overflow_dropped={poster.dropped_overflow} rejected_dropped={poster.dropped_rejected}"
          + (" (dry run: nothing sent)" if a.dry_run else f" | {poster.latency()}"))


if __name__ == "__main__":
    main()
