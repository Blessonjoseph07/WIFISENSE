"""
Inference for the exported WiFall random forest (pure numpy, no scikit-learn, no pickle).

The model file is plain JSON written by experiments/wifall/train_deployable_model.py. Besides the trees it records what
the model was trained on and how it scored in a person-independent test, so the application can show those limits
instead of hiding them.

What the output means: a score in 0..1 from the forest ("share of trees voting fall-like"). It is an UNCALIBRATED
heuristic score. It is NOT a probability that someone has fallen, and it was measured in one room with one
transmitter. The application never uses it to claim a fall was detected; it can only raise a "Possible fall" that
requires human verification.
"""
import json
import os
import threading
from typing import Dict, List, Optional

import numpy as np

from app.services.csi_features import FEATURE_NAMES

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "wifall_rf_v2.json")
FALL_SCORE_THRESHOLD = 0.5  # same decision rule as sklearn's predict() for the binary forest used in the experiments

_lock = threading.Lock()
_model: Optional[Dict] = None
_load_error: Optional[str] = None


def _load() -> Optional[Dict]:
    global _model, _load_error
    with _lock:
        if _model is not None or _load_error is not None:
            return _model
        try:
            with open(MODEL_PATH, "r", encoding="utf-8") as fh:
                model = json.load(fh)
            if model.get("features") != FEATURE_NAMES:
                raise ValueError("model feature list does not match app.services.csi_features.FEATURE_NAMES")
            for tree in model["trees"]:
                tree["feature"] = np.asarray(tree["feature"], dtype=np.int32)
                tree["threshold"] = np.asarray(tree["threshold"], dtype=np.float64)
                tree["left"] = np.asarray(tree["left"], dtype=np.int32)
                tree["right"] = np.asarray(tree["right"], dtype=np.int32)
                tree["p_fall"] = np.asarray(tree["p_fall"], dtype=np.float64)
            _model = model
        except Exception as exc:  # a missing or broken model must never break ingestion
            _load_error = f"{type(exc).__name__}: {exc}"
        return _model


def model_info() -> Dict:
    """Metadata only (no trees): provenance and the measured, person-independent performance."""
    model = _load()
    if model is None:
        return {"available": False, "error": _load_error}
    meta = {k: v for k, v in model.items() if k != "trees"}
    meta["available"] = True
    meta["n_trees"] = len(model["trees"])
    return meta


def fall_score(vec: np.ndarray) -> Optional[float]:
    """Share of trees whose leaf says fall-like, averaged as leaf probabilities (sklearn's predict_proba[:, 1])."""
    model = _load()
    if model is None:
        return None
    x = np.asarray(vec, dtype=np.float32)  # sklearn trees compare in float32; match it exactly
    total = 0.0
    for tree in model["trees"]:
        node = 0
        feature, threshold, left, right = tree["feature"], tree["threshold"], tree["left"], tree["right"]
        while feature[node] >= 0:
            node = left[node] if x[feature[node]] <= threshold[node] else right[node]
        total += tree["p_fall"][node]
    return float(total / len(model["trees"]))
