"""
CSI window features (numpy only).

These are the "V2" features of the WiFall experiments (see experiments/wifall/README.md): explainable statistics of
the amplitude and sanitised phase of one window of raw CSI. The experiment scripts and the running application use this
single implementation so that training and inference cannot drift apart.

Input  : array of shape (n_packets, 104) holding (I, Q) pairs for 52 subcarriers, as sent by an ESP32-S3.
Output : a vector in FEATURE_NAMES order.

Nothing here claims what a window "means". Turning features into a label is the model's job, and the model's
limits are documented next to it.
"""
from typing import Dict, List, Tuple

import numpy as np

N_SUBCARRIERS = 52
IQ_LEN = N_SUBCARRIERS * 2
FS = 84.0  # median packet rate measured on WiFall (Hz); used only to place spectral band edges

# Order matters: it is the column order the model was trained with.
FEATURE_NAMES: List[str] = [
    "motion_mean", "motion_median", "motion_max", "motion_rel",
    "burst_max", "burst_mean", "burst_std", "burst_ratio", "burst_pos", "burst_frac",
    "diff_mean", "diff_peak", "diff_peak_rel",
    "band_0.5_2", "band_2_5", "band_5_10", "band_10_20", "band_20_40",
    "pc1_frac", "level_cv",
    "seg_max_over_mean", "seg_entropy", "seg_argmax", "seg_first_vs_last",
    "dz_kurtosis", "dz_skew", "max_smoothed_slope", "acf_5", "acf_10", "acf_20",
    "pc1_kurtosis", "pc1_var_rel", "grp_motion_lo", "grp_motion_mid", "grp_motion_hi",
    "phase_std_mean", "phase_diff_mean", "phase_diff_peak_ratio",
]

MIN_PACKETS = 100  # below this the statistics are meaningless


def _kurt(x) -> float:
    x = np.asarray(x, dtype=np.float64)
    s = x.std()
    return float(((x - x.mean()) ** 4).mean() / (s ** 4 + 1e-12)) if s > 0 else 0.0


def _skew(x) -> float:
    x = np.asarray(x, dtype=np.float64)
    s = x.std()
    return float(((x - x.mean()) ** 3).mean() / (s ** 3 + 1e-12)) if s > 0 else 0.0


def _autocorr(z, lag: int) -> float:
    z = z - z.mean()
    d = (z * z).sum() + 1e-12
    return float((z[:-lag] * z[lag:]).sum() / d)


def sanitized_phase(I: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """Phase per packet, unwrapped across subcarriers, with the linear trend (timing/frequency offsets) removed."""
    ph = np.unwrap(np.arctan2(Q, I), axis=1)
    k = np.arange(ph.shape[1])
    out = np.empty_like(ph)
    for t in range(ph.shape[0]):
        a, b = np.polyfit(k, ph[t], 1)
        out[t] = ph[t] - (a * k + b)
    return out


def extract_features(iq: np.ndarray) -> Tuple[List[str], np.ndarray]:
    iq = np.asarray(iq, dtype=np.float32)
    if iq.ndim != 2 or iq.shape[1] != IQ_LEN:
        raise ValueError(f"expected (n_packets, {IQ_LEN}) I/Q values, got {iq.shape}")
    if iq.shape[0] < MIN_PACKETS:
        raise ValueError(f"need at least {MIN_PACKETS} packets, got {iq.shape[0]}")

    I, Q = iq[:, 0::2], iq[:, 1::2]
    A = np.sqrt(I * I + Q * Q)
    n = A.shape[0]
    f: Dict[str, float] = {}

    level = A.mean()
    sc_std = A.std(axis=0)
    f["motion_mean"] = sc_std.mean()
    f["motion_median"] = float(np.median(sc_std))
    f["motion_max"] = sc_std.max()
    f["motion_rel"] = sc_std.mean() / (level + 1e-6)

    m = A.mean(axis=1)
    z = (m - m.mean()) / (m.mean() + 1e-6)
    w, s = 20, 5
    wv = np.array([z[i:i + w].var() for i in range(0, n - w + 1, s)])
    f["burst_max"] = wv.max()
    f["burst_mean"] = wv.mean()
    f["burst_std"] = wv.std()
    f["burst_ratio"] = wv.max() / (np.median(wv) + 1e-9)
    f["burst_pos"] = float(np.argmax(wv)) / max(1, len(wv) - 1)
    f["burst_frac"] = float((wv > 1.5 * np.median(wv)).mean())

    d = np.abs(np.diff(A, axis=0))
    f["diff_mean"] = d.mean()
    f["diff_peak"] = d.mean(axis=1).max()
    f["diff_peak_rel"] = f["diff_peak"] / (d.mean() + 1e-9)

    spec = np.abs(np.fft.rfft(z * np.hanning(n))) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0 / FS)
    tot = spec[1:].sum() + 1e-12
    for lo, hi in [(0.5, 2), (2, 5), (5, 10), (10, 20), (20, 40)]:
        f[f"band_{lo}_{hi}"] = spec[(freqs >= lo) & (freqs < hi)].sum() / tot

    Ac = A - A.mean(axis=0)
    U, sv, _ = np.linalg.svd(Ac, full_matrices=False)
    f["pc1_frac"] = (sv[0] ** 2) / ((sv ** 2).sum() + 1e-9)
    f["level_cv"] = m.std() / (m.mean() + 1e-6)

    seg = np.array([x.var() for x in np.array_split(z, 5)])
    f["seg_max_over_mean"] = seg.max() / (seg.mean() + 1e-12)
    p = seg / (seg.sum() + 1e-12)
    f["seg_entropy"] = float(-(p * np.log(p + 1e-12)).sum())
    f["seg_argmax"] = float(np.argmax(seg)) / 4.0
    f["seg_first_vs_last"] = (seg[:2].mean() + 1e-12) / (seg[-2:].mean() + 1e-12)
    dz = np.diff(z)
    f["dz_kurtosis"] = _kurt(dz)
    f["dz_skew"] = _skew(dz)
    zs = np.convolve(z, np.ones(5) / 5, mode="same")
    f["max_smoothed_slope"] = float(np.abs(np.diff(zs)).max())
    for lag in (5, 10, 20):
        f[f"acf_{lag}"] = _autocorr(z, lag)
    pc1 = U[:, 0] * sv[0]
    f["pc1_kurtosis"] = _kurt(pc1)
    f["pc1_var_rel"] = float(pc1.var() / (A.var() * n + 1e-9))
    for name, sl in (("lo", slice(0, 17)), ("mid", slice(17, 35)), ("hi", slice(35, 52))):
        f[f"grp_motion_{name}"] = A[:, sl].std(axis=0).mean() / (A[:, sl].mean() + 1e-6)

    ph = sanitized_phase(I, Q)
    f["phase_std_mean"] = float(ph.std(axis=0).mean())
    f["phase_diff_mean"] = float(np.abs(np.diff(ph, axis=0)).mean())
    pdm = np.abs(np.diff(ph, axis=0)).mean(axis=1)
    f["phase_diff_peak_ratio"] = float(pdm.max() / (np.median(pdm) + 1e-9))

    vec = np.array([f[k] for k in FEATURE_NAMES], dtype=np.float64)
    if not np.all(np.isfinite(vec)):
        raise ValueError("non-finite feature value")
    return FEATURE_NAMES, vec
