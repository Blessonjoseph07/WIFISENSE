"""
Phase 2: an in-room model of what is happening between the boards, learned from this room's own labelled recordings.

Why this exists: a model trained on someone else's data (the fall model, WiFall) does not transfer to a busy classroom. Wi-Fi
CSI depends strongly on the room, the board placement and the people in it. So instead of shipping a generic model, the operator
records short labelled segments in THIS room ("empty", "someone still", "someone walking", "few people", "busy"), and a small
classifier learns to tell the recorded ones apart. Only the situations that were recorded are ever predicted.

What it is and is not
  * It estimates a room STATE from the signal of one transmitter-receiver pair. It does not count people, locate them or
    identify them.
  * It is trained on what was recorded, at this board placement, on that day. If the room or the board position changes, record again.
  * It is evaluated honestly: the last 30% of every recording is held out (never used for training) and the accuracy on that
    held-out part is reported, with a confusion matrix. If it is not good enough the model is marked not reliable.

The model is multinomial logistic regression on the features of each 50-packet block, in plain numpy (no extra dependencies).
Two kinds of feature:
  * motion (how much the signal fluctuates inside the block): separates moving from not moving;
  * static (mean RSSI and the normalised SHAPE of the amplitude across subcarriers): a body sitting in the radio path absorbs and
    reflects part of the signal, which changes that shape even when the person does not move. Without these a person sitting
    still looks exactly like an empty room, because neither fluctuates.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from app.services import csi_physics

LABELS = ("empty", "still", "walking", "few", "busy")
LABEL_TEXT = {"empty": "Empty room", "still": "Someone sitting or lying still", "walking": "Someone walking",
              "few": "A few people", "busy": "Busy"}
BLOCK = 50
PROFILE_BANDS = 8          # the 52 subcarriers grouped into 8 bands for the amplitude-shape features
FEATURES = ("variation", "variation_p90", "rssi_std", "motion_energy", "rssi_mean") + tuple(f"shape_{i}" for i in range(PROFILE_BANDS))
HOLDOUT = 0.30
GAP_BLOCKS = 2             # blocks dropped between the training part and the held-out part, so neighbours do not leak
MIN_BLOCKS_PER_LABEL = 20
MIN_HELDOUT_PER_LABEL = 6
RELIABLE_ACCURACY = 0.75
PREDICT_BLOCKS = 10
MAX_SESSIONS_PER_LABEL = 12
UNVERIFIED_ACCURACY = 0.6  # confidence shrink for a model never tested on a recording it did not see


def compatible(blocks) -> List[List[float]]:
    """Blocks recorded with the current feature set (recordings made before the feature set changed are ignored)."""
    return [b for b in blocks if len(b) == len(FEATURES)]


def block_features(records) -> List[List[float]]:
    """len(FEATURES) numbers per block of BLOCK consecutive packets (oldest first)."""
    amps, rssis = [], []
    for r in records:
        data = r.csi_data if isinstance(r.csi_data, dict) else {}
        ap = csi_physics.iq_to_amp_phase(data.get("iq"))
        if ap and ap.get("amplitude"):
            amps.append(ap["amplitude"])
            rssis.append(float(r.rssi))
    out = []
    for i in range(0, len(amps) - BLOCK + 1, BLOCK):
        a = np.asarray(amps[i:i + BLOCK], dtype=float)
        mean = a.mean(axis=0) + 1e-9
        per_sc = a.std(axis=0) / mean
        motion = np.abs(np.diff(a, axis=0)).mean() / float(a.mean() + 1e-9)
        bands = np.array([band.mean() for band in np.array_split(mean, PROFILE_BANDS)])
        shape = bands / bands.sum()               # normalised, so receiver gain changes do not move it
        r = rssis[i:i + BLOCK]
        out.append([float(per_sc.mean()), float(np.percentile(per_sc, 90)), float(np.std(r)), float(motion), float(np.mean(r))]
                   + [float(v) for v in shape])
    return out


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _fit(X: np.ndarray, y: np.ndarray, k: int, iters: int = 600, lr: float = 0.3, l2: float = 1e-3):
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-9
    Z = (X - mu) / sd
    n, f = Z.shape
    W, b = np.zeros((f, k)), np.zeros(k)
    Y = np.eye(k)[y]
    counts = np.bincount(y, minlength=k).astype(float)
    w = (n / (k * np.maximum(counts, 1)))[y][:, None]          # balance the classes
    for _ in range(iters):
        P = _softmax(Z @ W + b)
        G = (P - Y) * w
        W -= lr * ((Z.T @ G) / n + l2 * W)
        b -= lr * G.mean(axis=0)
    return {"mu": mu.tolist(), "sd": sd.tolist(), "W": W.tolist(), "b": b.tolist()}


def _proba(model: Dict[str, Any], X: np.ndarray) -> np.ndarray:
    Z = (X - np.asarray(model["mu"])) / np.asarray(model["sd"])
    return _softmax(Z @ np.asarray(model["W"]) + np.asarray(model["b"]))


def split_session(blocks: List[List[float]]):
    n = len(blocks)
    cut = int(round(n * (1 - HOLDOUT)))
    return blocks[:cut], blocks[min(n, cut + GAP_BLOCKS):]


def train(sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """sessions: label -> [{"blocks": [[f0..f3], ...], ...}]. Returns {"model", "evaluation"} or raises ValueError with a plain reason."""
    sessions = {l: [dict(s, blocks=compatible(s["blocks"])) for s in v] for l, v in sessions.items()}
    labels = [l for l in LABELS if sum(len(s["blocks"]) for s in sessions.get(l, [])) >= MIN_BLOCKS_PER_LABEL]
    if len(labels) < 2:
        have = {l: sum(len(s["blocks"]) for s in sessions.get(l, [])) for l in LABELS}
        raise ValueError(f"Need at least two situations with {MIN_BLOCKS_PER_LABEL}+ blocks (about {MIN_BLOCKS_PER_LABEL * BLOCK // 90 + 1} s each). Recorded so far: {have}.")
    idx = {l: i for i, l in enumerate(labels)}
    k = len(labels)
    # Honest check: with 2+ recordings of every situation, each recording is tested by a model trained WITHOUT it (the end
    # of a recording looks too much like its start, so testing on it flatters the model). With fewer recordings the
    # end-of-recording check is the only one possible, and the model is never called reliable on it.
    across = all(len(sessions[l]) >= 2 for l in labels)
    truth_l, pred_l = [], []
    if across:
        method = "leave-one-recording-out"
        for l in labels:
            for i, s in enumerate(sessions[l]):
                rest = [(l2, s2) for l2 in labels for j, s2 in enumerate(sessions[l2]) if not (l2 == l and j == i)]
                m = _fit(np.asarray([b for _, s2 in rest for b in s2["blocks"]]),
                         np.asarray([idx[l2] for l2, s2 in rest for _ in s2["blocks"]], dtype=int), k)
                pred_l += _proba(m, np.asarray(s["blocks"])).argmax(axis=1).tolist()
                truth_l += [idx[l]] * len(s["blocks"])
    else:
        method = "end-of-recording"
        tr_X, tr_y, te_X = [], [], []
        for l in labels:
            for s in sessions[l]:
                a, b = split_session(s["blocks"])
                tr_X += a; tr_y += [idx[l]] * len(a)
                te_X += b; truth_l += [idx[l]] * len(b)
        first = _fit(np.asarray(tr_X), np.asarray(tr_y, dtype=int), k)
        pred_l = _proba(first, np.asarray(te_X)).argmax(axis=1).tolist() if te_X else []
    truth, pred = np.asarray(truth_l, dtype=int), np.asarray(pred_l, dtype=int)
    held = np.bincount(truth, minlength=k) if len(truth) else np.zeros(k, int)
    cm = np.zeros((k, k), dtype=int)
    for t, p in zip(truth, pred):
        cm[t, p] += 1
    acc = float((pred == truth).mean()) if len(truth) else 0.0
    recall = {l: (round(float(cm[idx[l], idx[l]] / cm[idx[l]].sum()), 3) if cm[idx[l]].sum() else None) for l in labels}
    majority = float(held.max() / held.sum()) if held.sum() else 0.0
    enough = bool(held.min() >= MIN_HELDOUT_PER_LABEL)
    reliable = bool(across and enough and acc >= RELIABLE_ACCURACY and acc > majority + 0.1)
    if reliable:
        reason = None
    elif not across:
        thin = [LABEL_TEXT[l] for l in labels if len(sessions[l]) < 2]
        reason = ("each situation needs at least 2 recordings, so it can be tested on a recording it never saw "
                  f"(record again: {', '.join(thin)})")
    elif not enough:
        reason = "too few blocks to judge: record longer"
    else:
        reason = "it did not separate the situations well enough on recordings it had not seen"
    # final model: all recorded data. Its displayed confidence is shrunk by the measured error (see predict()); an
    # unverified model (one recording per situation) is shrunk as if it were right only 60% of the time.
    all_X = np.asarray([b for l in labels for s in sessions[l] for b in s["blocks"]])
    all_y = np.asarray([idx[l] for l in labels for s in sessions[l] for _ in s["blocks"]], dtype=int)
    model = _fit(all_X, all_y, k)
    model["labels"] = labels
    model["calibration_acc"] = round(acc if across else min(acc, UNVERIFIED_ACCURACY), 3)
    return {
        "model": model,
        "evaluation": {
            "heldout_accuracy": round(acc, 3), "majority_baseline": round(majority, 3), "heldout_blocks": {l: int(held[idx[l]]) for l in labels},
            "recall": recall, "confusion": {"labels": labels, "matrix": cm.tolist()},
            "trained_blocks": {l: sum(len(s["blocks"]) for s in sessions[l]) for l in labels},
            "recordings": {l: len(sessions[l]) for l in labels},
            "method": method,
            "reliable": reliable,
            "reason": reason,
            "note": ("Each recording was tested by a model trained without it. One room, one board placement." if across else
                     "Only the last 30% of each recording was held out, which flatters the model: record every situation "
                     "at least twice for an honest number."),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def model_compatible(model: Optional[Dict[str, Any]]) -> bool:
    return bool(model) and len(model.get("mu") or []) == len(FEATURES)


def predict(model: Dict[str, Any], feats: List[List[float]]) -> Optional[Dict[str, Any]]:
    if not feats or not model_compatible(model):
        return None
    recent = np.asarray(feats[-PREDICT_BLOCKS:], dtype=float)
    labels = model["labels"]
    raw = _proba(model, recent).mean(axis=0)
    # The classifier's own probability is overconfident on small recordings. Mix it with "no idea" in proportion to the
    # error measured on unseen recordings, so a model that is right 80% of the time cannot show 99%.
    cal = float(model.get("calibration_acc", UNVERIFIED_ACCURACY))
    p = cal * raw + (1.0 - cal) / len(labels)
    k = int(p.argmax())
    return {"label": labels[k], "text": LABEL_TEXT[labels[k]], "confidence": round(float(p[k]), 3),
            "probabilities": {l: round(float(v), 3) for l, v in zip(labels, p)}, "blocks_used": int(len(recent))}
