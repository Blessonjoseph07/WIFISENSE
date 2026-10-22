"""
ESP32-S3 CSI emulator for development. Posts the SAME packet format the real firmware must send, to a device that is
registered as DEMO (allowed_source="simulated"), so the Live Stream panel can be built and shown before hardware exists.
Everything it sends is badged DEMO by the application. It never targets a LIVE HARDWARE device.

    python tools/esp32_emulator.py --api http://127.0.0.1:8000 --token TK-ESP32-... --activity walking

The token is the one-time hardware_token returned when the DEMO device was registered (POST /devices).
Activities: empty, sitting, walking, fall (cycles: still, burst, still).
Requires numpy.
"""
import argparse
import json
import math
import time
import urllib.error
import urllib.request

import numpy as np

SUBCARRIER_INDEX = list(range(-26, 0)) + list(range(1, 27))
SPACING_HZ = 312_500.0
C = 299_792_458.0


def channel_hz(ch):
    return (2407 + 5 * ch) * 1e6


class Channel:
    """Toy multipath channel: a few static paths plus one moving scatterer whose delay changes with time."""

    def __init__(self, channel=6, seed=1):
        self.rng = np.random.default_rng(seed)
        self.fc = channel_hz(channel)
        self.k = np.array(SUBCARRIER_INDEX, dtype=float)
        self.static = [(self.rng.uniform(0.5, 1.0), self.rng.uniform(8, 40) / C, self.rng.uniform(0, 6.28)) for _ in range(4)]
        self.t0 = time.time()

    def csi(self, activity, t):
        f = self.fc + self.k * SPACING_HZ
        h = np.zeros(len(f), dtype=complex)
        for a, tau, ph in self.static:
            h += a * np.exp(-1j * (2 * math.pi * f * tau) + 1j * ph)
        mover = 0.0
        speed = 0.0
        if activity == "walking":
            speed = 1.0
            mover = 0.6
        elif activity == "sitting":
            speed = 0.05
            mover = 0.25
        elif activity == "fall":
            cyc = t % 12.0
            if 4.0 <= cyc < 5.5:
                speed, mover = 2.5, 1.0
            elif cyc >= 5.5:
                speed, mover = 0.0, 0.15
            else:
                speed, mover = 0.1, 0.25
        if mover:
            path = 12.0 + speed * t + 0.3 * math.sin(2 * math.pi * 0.7 * t)
            h += mover * np.exp(-1j * 2 * math.pi * f * path / C)
        h += (self.rng.normal(0, 0.02, len(f)) + 1j * self.rng.normal(0, 0.02, len(f)))
        return h


def to_iq(h, gain=40.0):
    """104 integers (I0, Q0, I1, Q1, ...) clipped to the int8 range a real ESP32 reports."""
    iq = np.empty(2 * len(h))
    iq[0::2] = np.clip(np.round(h.real * gain), -127, 127)
    iq[1::2] = np.clip(np.round(h.imag * gain), -127, 127)
    return [int(v) for v in iq]


def post(api, token, packets):
    req = urllib.request.Request(
        f"{api}/sensing/ingest",
        data=json.dumps({"packets": packets}).encode(),
        headers={"Content-Type": "application/json", "X-Device-Token": token},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--token", required=True)
    ap.add_argument("--activity", default="walking", choices=["empty", "sitting", "walking", "fall"])
    ap.add_argument("--rate", type=float, default=50.0, help="packets per second")
    ap.add_argument("--batch", type=int, default=10, help="packets per HTTP request")
    ap.add_argument("--channel", type=int, default=6)
    ap.add_argument("--seconds", type=float, default=0, help="0 = run until Ctrl+C")
    args = ap.parse_args()

    ch = Channel(args.channel)
    seq = 0
    start = time.time()
    period = args.batch / args.rate
    print(f"emulating {args.activity} at {args.rate:g} pkt/s to {args.api} (DEMO device)")
    try:
        while args.seconds == 0 or time.time() - start < args.seconds:
            t_batch = time.time()
            packets = []
            for i in range(args.batch):
                t = t_batch - start + i / args.rate
                h = ch.csi(args.activity, t)
                amp = float(np.mean(np.abs(h)))
                rssi = int(round(-62 + 60 * math.log10(max(amp, 1e-3) / 2.0) + float(ch.rng.normal(0, 0.8))))
                packets.append({
                    "sequence_number": seq & 0xFFFF, "rssi": max(-120, min(-1, rssi)), "noise_floor": -92,
                    "subcarrier_count": 52, "bandwidth_mhz": 20, "channel": args.channel,
                    "provenance": "simulated",
                    "csi_data": {"iq": to_iq(h), "src_mac": "24:0A:C4:00:00:01", "rate": 11, "sig_mode": 0, "cwb": 0},
                })
                seq += 1
            try:
                status, body = post(args.api, args.token, packets)
                print(f"\rsent {seq} packets (HTTP {status})", end="", flush=True)
            except urllib.error.HTTPError as e:
                print(f"\nHTTP {e.code}: {e.read().decode()[:200]}")
                break
            time.sleep(max(0.0, period - (time.time() - t_batch)))
    except KeyboardInterrupt:
        pass
    print("\nstopped")


if __name__ == "__main__":
    main()
