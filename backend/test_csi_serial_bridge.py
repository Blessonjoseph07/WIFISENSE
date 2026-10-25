"""
CSI SERIAL BRIDGE TEST SUITE (no server, no hardware)
=====================================================
tools/csi_serial_bridge.py turns the receiver firmware's serial lines into API packets. These checks make sure it
accepts exactly what the firmware prints, drops everything else, never changes values, and stops when the firmware's I/Q
conversion disagrees with the reference conversion.
"""
import cmath
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import csi_buffer_to_iq as ref  # noqa: E402
import csi_serial_bridge as bridge  # noqa: E402

TX = "1a:00:00:00:00:00"


def fake_buffer(seed=0):
    """A 128-value ESP-IDF style buffer: (imag, real) per slot, slots 0..31 then -32..-1; guard and DC slots are zero."""
    buf = [0] * 128
    for k in ref.USED:
        h = cmath.rect(40 + 8 * math.sin(k / 5.0 + seed), 0.2 * k + seed)
        s = ref.slot(k)
        buf[2 * s], buf[2 * s + 1] = int(round(h.imag)), int(round(h.real))
    return buf


def hx(vals):
    return "".join(f"{v & 0xFF:02x}" for v in vals)


def iq_line(seq, iq, mac=TX, sig_mode=0, cwb=0, rssi=-55):
    return f"CSI_IQ,{seq},{mac},{rssi},11,{sig_mode},0,{cwb},-92,11,0,{hx(iq)}"


def raw_line(seq, buf):
    return f"CSI_RAW,{seq},{hx(buf)}"


def run_bridge(lines, *extra):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
        path = fh.name
    try:
        return subprocess.run([sys.executable, str(TOOLS / "csi_serial_bridge.py"), "--file", path, "--dry-run", *extra],
                              capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(path)


def run():
    buf = fake_buffer()
    iq = ref.convert(buf)
    assert not ref.check_layout(buf) and len(iq) == 104

    print("--- parsing")
    p = bridge.parse_iq_line(iq_line(7, iq))
    assert p and p["seq"] == 7 and p["iq"] == iq and p["mac"] == TX and p["channel"] == 11
    pkt = bridge.to_packet(p, "live")
    assert pkt["subcarrier_count"] == 52 and pkt["bandwidth_mhz"] == 20 and pkt["provenance"] == "live"
    assert pkt["csi_data"]["iq"] == iq and pkt["csi_data"]["src_mac"] == TX
    assert not {"label", "activity", "class", "event_type"} & set(pkt["csi_data"]), "no labels may ever be added"
    assert bridge.parse_iq_line(iq_line(1, iq[:-2])) is None, "wrong length"
    assert bridge.parse_iq_line(iq_line(1, iq)[:-3] + "zz0") is None, "non-hex payload"
    assert bridge.parse_iq_line(iq_line(1, iq).replace(",11,0,", ",11,0,0,", 1)) is None, "extra field"
    assert bridge.parse_iq_line(iq_line(1, iq, sig_mode=1)) is None, "HT frame"
    assert bridge.parse_iq_line(iq_line(1, iq, cwb=1)) is None, "40 MHz frame"
    assert bridge.parse_iq_line(iq_line(1, iq, rssi=5)) is None, "impossible rssi"
    assert bridge.parse_iq_line("I (123) wifisense_rx: RX ready") is None
    assert bridge.parse_iq_line(iq_line(1, iq)[:-1]) is None, "truncated line"
    assert bridge.parse_raw_line(raw_line(3, buf))["buf"] == buf
    print("[PASS] accepts the firmware's exact format; rejects bad length, range, HT/40 MHz, rssi, noise and truncation")

    print("--- reference conversion vs the firmware's")
    good = [iq_line(i, ref.convert(fake_buffer(i))) for i in range(5)]
    lines = [good[0], raw_line(0, fake_buffer(0)), *good[1:]] + ["garbage", iq_line(9, iq, mac="aa:bb:cc:dd:ee:ff")]
    r = run_bridge(lines)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "read=5" in r.stdout and "sent=5" in r.stdout and "dropped_format=1" in r.stdout and "raw_checks_ok=1" in r.stdout, r.stdout
    print("[PASS] 5 packets read and 'sent' (dry run), 1 foreign-MAC packet dropped, raw cross-check passed")

    swapped = [iq[i + 1] if i % 2 == 0 else iq[i - 1] for i in range(104)]   # firmware forgot to swap imag/real back
    r = run_bridge([iq_line(0, swapped), raw_line(0, buf)])
    assert r.returncode != 0 and "DISAGREES" in (r.stdout + r.stderr), r.stdout + r.stderr
    r = run_bridge([iq_line(0, iq), raw_line(0, [0] * 256)])
    assert r.returncode != 0 and "not the supported layout" in (r.stdout + r.stderr), r.stdout + r.stderr
    print("[PASS] wrong imag/real order or an HT40-length raw buffer stops the bridge with a clear message")

    r = run_bridge([iq_line(0, iq)], "--tx-mac", "7c:4f:ad:26:05:78")
    assert "read=0" in r.stdout and "dropped_format=1" in r.stdout, r.stdout
    print("[PASS] only the configured transmitter's packets are used")

    # OLED line the bridge writes back to the receiver
    assert bridge.display_lines({"movement_state": "MOVEMENT", "room_state": {"label": "walking", "confidence": 0.874, "reliable": True}}) \
        == "WS_STATE,PRESENCE+MOVE,WALKING 87%\n"
    assert bridge.display_lines({"movement_state": "QUIET", "room_state": {"label": "still", "confidence": 0.6, "reliable": False}}) \
        == "WS_STATE,NO PRESENCE,STILL 60%?\n"
    assert bridge.display_lines({"movement_state": "STALE", "room_state": None}) == "WS_STATE,NOT SENDING,NOT TRAINED\n"
    assert bridge.display_lines({}) == "WS_STATE,NO DATA,NOT TRAINED\n"
    assert bridge.display_lines({"movement_state": "MOVEMENT", "room_state": {"label": "moving", "confidence": None, "reliable": True}}) \
        == "WS_STATE,PRESENCE+MOVE,MOVING\n"
    assert bridge.display_lines({"movement_state": "MOVEMENT", "room_state": {"label": "presence", "confidence": 0.9, "reliable": True}}) \
        == "WS_STATE,PRESENCE+MOVE,PRESENCE 90%\n"
    print("[PASS] display line: presence + learned state, '?' when the model is not reliable, never a comma or non-ASCII")


if __name__ == "__main__":
    print("=== CSI SERIAL BRIDGE TESTS ===")
    run()
    print("\nALL CSI SERIAL BRIDGE TESTS PASSED")
