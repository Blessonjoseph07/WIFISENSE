"""
Reference conversion of an ESP32-S3 CSI buffer into the API's 104-value I/Q vector, to cross-check the C firmware.

Supported layout (the one the API and the fall model expect): 20 MHz channel, non-HT frame, legacy long training field
only (lltf_en=true, htltf_en=false). The ESP-IDF buffer is 128 int8 values = 64 subcarrier slots of (imag, real), slot order
0..31 then -32..-1. The API wants the 52 used subcarriers (-26..-1, 1..26) as (real, imag) pairs: 104 values.

Usage
  python tools/csi_buffer_to_iq.py --selftest
  python tools/csi_buffer_to_iq.py --buf "0,0,12,-5,..."     # 128 comma-separated int8 values from a serial dump
Compare the output with what the firmware sends in csi_data.iq for the same packet: they must be identical.

It refuses anything that is not the expected layout (length other than 128, energy in the guard slots, a flat spectrum) so
a wrong CSI configuration is reported instead of silently producing garbled data.
"""
import argparse
import sys
from typing import List

USED = list(range(-26, 0)) + list(range(1, 27))
SLOTS = 64


def slot(k: int) -> int:
    return k if k >= 0 else SLOTS + k


def convert(buf: List[int]) -> List[int]:
    if len(buf) != 2 * SLOTS:
        raise ValueError(f"expected {2 * SLOTS} int8 values (20 MHz, legacy LTF only), got {len(buf)}. "
                         f"HT-LTF, STBC or 40 MHz CSI has a different length and slot order and is NOT supported by the API detector.")
    if any(not -128 <= v <= 127 for v in buf):
        raise ValueError("values must be int8 (-128..127)")
    out: List[int] = []
    for k in USED:
        s = slot(k)
        out.append(buf[2 * s + 1])   # real  -> I
        out.append(buf[2 * s])       # imag  -> Q
    return out


def check_layout(buf: List[int]) -> List[str]:
    """Problems that mean the buffer is not what the converter assumes."""
    problems = []
    unused = [0] + list(range(27, 32)) + list(range(-32, -26))    # DC and the guard slots carry no subcarrier
    energy_unused = sum(abs(buf[2 * slot(k)]) + abs(buf[2 * slot(k) + 1]) for k in unused)
    energy_used = sum(abs(buf[2 * slot(k)]) + abs(buf[2 * slot(k) + 1]) for k in USED)
    if energy_used == 0:
        problems.append("all used subcarriers are zero: no CSI in this buffer (wrong frame type, or first_word_invalid)")
    elif energy_unused > 0.15 * energy_used:
        problems.append(f"guard/DC slots hold {energy_unused / energy_used:.0%} of the energy: the slot order or layout is not the assumed one")
    return problems


def selftest() -> None:
    import cmath
    import math
    h = {k: cmath.rect(30 + 5 * math.sin(k / 4.0), 0.3 * k) for k in USED}
    buf = [0] * (2 * SLOTS)
    for k in USED:
        buf[2 * slot(k)] = int(round(h[k].imag))        # ESP-IDF order: imag first
        buf[2 * slot(k) + 1] = int(round(h[k].real))
    assert not check_layout(buf), check_layout(buf)
    iq = convert(buf)
    assert len(iq) == 104
    for n, k in enumerate(USED):
        assert iq[2 * n] == int(round(h[k].real)) and iq[2 * n + 1] == int(round(h[k].imag)), (k, n)
    # a buffer with the slot order wrong must be flagged, not converted silently
    bad = [0] * (2 * SLOTS)
    for n, k in enumerate(USED):
        bad[2 * n], bad[2 * n + 1] = buf[2 * slot(k)], buf[2 * slot(k) + 1]   # packed in -26..26 order instead of 0..31,-32..-1
    assert check_layout(bad), "a wrongly ordered buffer should be reported"
    try:
        convert([0] * 128 + [1] * 128)
        raise AssertionError("HT40-length buffer must be rejected")
    except ValueError:
        pass
    print("selftest OK: imag/real swap, slot order 0..31,-32..-1 -> -26..-1,1..26, layout checks, HT40 length rejected")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--buf", help="comma-separated int8 values of one CSI buffer")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.buf:
        ap.error("give --buf or --selftest")
    buf = [int(x) for x in a.buf.replace(" ", "").split(",") if x != ""]
    try:
        iq = convert(buf)
    except ValueError as exc:
        sys.exit(f"REJECTED: {exc}")
    for p in check_layout(buf):
        print("WARNING:", p)
    print(f"iq ({len(iq)} values):")
    print(",".join(str(v) for v in iq))


if __name__ == "__main__":
    main()
