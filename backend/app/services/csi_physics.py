"""
Quantities that can honestly be derived from raw CSI and from the radio channel (numpy only).

Everything here is computed from what a device really sent, or from the channel number it reports. Nothing is a
position: one transmitter-receiver pair measures how the channel between those two radios changes. It cannot place a
person at x/y coordinates (that needs several receivers); this module never pretends otherwise.
"""
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from app.services.csi_features import IQ_LEN, N_SUBCARRIERS

SPEED_OF_LIGHT = 299_792_458.0
SUBCARRIER_SPACING_MHZ = 20.0 / 64  # 802.11 OFDM, 20 MHz channel: 312.5 kHz
# Legacy long training field: 52 used subcarriers, indices -26..-1 and 1..26 (index 0 is DC and is not sent).
SUBCARRIER_INDEX: List[int] = list(range(-26, 0)) + list(range(1, 27))


def channel_center_mhz(channel: Optional[int]) -> Optional[float]:
    """Center frequency of a Wi-Fi channel number: 2.4 GHz channels 1-14, otherwise 5 GHz numbering."""
    if channel is None:
        return None
    if 1 <= channel <= 13:
        return 2407.0 + 5.0 * channel
    if channel == 14:
        return 2484.0
    if channel >= 32:
        return 5000.0 + 5.0 * channel
    return None


def link_info(channel: Optional[int], bandwidth_mhz: Optional[int]) -> Dict[str, Any]:
    fc = channel_center_mhz(channel)
    info: Dict[str, Any] = {
        "channel": channel,
        "bandwidth_mhz": bandwidth_mhz,
        "center_frequency_mhz": fc,
        "wavelength_cm": None,
        "subcarrier_spacing_khz": SUBCARRIER_SPACING_MHZ * 1000.0,
        "subcarrier_index": SUBCARRIER_INDEX,
        "subcarrier_frequency_mhz": None,
        "subcarrier_wavelength_cm": None,
        "derived_from": "the channel number the device reported; not measured",
    }
    if fc:
        freqs = [round(fc + k * SUBCARRIER_SPACING_MHZ, 4) for k in SUBCARRIER_INDEX]
        info["wavelength_cm"] = round(SPEED_OF_LIGHT / (fc * 1e6) * 100.0, 3)
        info["subcarrier_frequency_mhz"] = freqs
        info["subcarrier_wavelength_cm"] = [round(SPEED_OF_LIGHT / (f * 1e6) * 100.0, 3) for f in freqs]
    return info


def iq_to_amp_phase(iq: Sequence[float]) -> Optional[Dict[str, List[float]]]:
    """One packet: 104 values (I0, Q0, I1, Q1, ...) -> amplitude and sanitised phase per subcarrier, or None."""
    if not isinstance(iq, (list, tuple)) or len(iq) != IQ_LEN:
        return None
    try:
        arr = np.asarray(iq, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if not np.all(np.isfinite(arr)):
        return None
    i, q = arr[0::2], arr[1::2]
    amp = np.hypot(i, q)
    ph = np.unwrap(np.arctan2(q, i))
    k = np.arange(N_SUBCARRIERS)
    a, b = np.polyfit(k, ph, 1)  # remove the linear trend caused by timing/frequency offsets
    return {"amplitude": [round(float(v), 3) for v in amp], "phase": [round(float(v), 4) for v in ph - (a * k + b)]}


def window_stats(packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Statistics over the packets of one live window. Each packet dict carries rssi, noise, seq, t (epoch s), amp."""
    out: Dict[str, Any] = {
        "packets": len(packets), "arrival_rate_hz": None, "packet_loss_pct": None,
        "rssi_mean_dbm": None, "rssi_std_db": None, "noise_floor_mean_dbm": None, "snr_db": None,
        "amplitude_mean": None, "amplitude_variation": None, "dominant_fluctuation_hz": None,
        "per_subcarrier_variation": None,
    }
    if not packets:
        return out
    rssi = np.array([p["rssi"] for p in packets], dtype=float)
    out["rssi_mean_dbm"] = round(float(rssi.mean()), 1)
    out["rssi_std_db"] = round(float(rssi.std()), 2)
    noise = [p["noise"] for p in packets if p.get("noise") is not None]
    if noise:
        out["noise_floor_mean_dbm"] = round(float(np.mean(noise)), 1)
        out["snr_db"] = round(float(rssi.mean() - np.mean(noise)), 1)

    times = np.array([p["t"] for p in packets if p.get("t") is not None], dtype=float)
    if len(times) > 1 and times[-1] > times[0]:
        out["arrival_rate_hz"] = round((len(times) - 1) / float(times[-1] - times[0]), 1)

    seqs = [p["seq"] for p in packets if p.get("seq") is not None]
    if len(seqs) > 1:
        span = max(seqs) - min(seqs) + 1
        if span > 0:
            out["packet_loss_pct"] = round(max(0.0, 100.0 * (1.0 - len(set(seqs)) / span)), 1)

    amps = [p["amp"] for p in packets if p.get("amp")]
    if amps:
        a = np.asarray(amps, dtype=float)  # (packets, subcarriers)
        out["amplitude_mean"] = round(float(a.mean()), 2)
        if len(a) >= 3:
            per_sc = a.std(axis=0) / (a.mean(axis=0) + 1e-9)
            out["per_subcarrier_variation"] = [round(float(v), 4) for v in per_sc]
            out["amplitude_variation"] = round(float(per_sc.mean()), 4)
            rate = out["arrival_rate_hz"]
            if rate and rate >= 8 and len(a) >= 24:
                level = a.mean(axis=1)
                level = level - level.mean()
                spec = np.abs(np.fft.rfft(level * np.hanning(len(level))))
                freqs = np.fft.rfftfreq(len(level), d=1.0 / rate)
                if len(spec) > 2:
                    spec[0] = 0.0
                    out["dominant_fluctuation_hz"] = round(float(freqs[int(np.argmax(spec))]), 2)
    return out
