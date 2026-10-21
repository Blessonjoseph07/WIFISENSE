"""
Train and export the deployable WiFall model (random forest on the V2 features, no per-person calibration).

Usage:  python train_deployable_model.py /path/to/WiFall  /path/to/output_dir  [--cache clips_iq.npz]
Needs numpy and scikit-learn (NOT part of the application's requirements).

Steps
  1. read the WiFall clips and compute features with the APPLICATION'S feature code (backend/app/services/csi_features.py)
  2. re-run the person-independent (leave-one-person-out) evaluation with EXACTLY the hyper-parameters being exported,
     so the accuracy recorded in the model file belongs to this model and not to a similar one
  3. train on all clips and export the forest as plain JSON (no pickle) to backend/app/ml/wifall_rf_v2.json
  4. check that the pure-numpy inference in the application reproduces scikit-learn's scores
"""
import argparse
import ast
import csv
import datetime
import json
import os
import sys

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", "..", "backend"))
sys.path.insert(0, BACKEND)
from app.services.csi_features import FEATURE_NAMES, extract_features  # noqa: E402

SEED = 0
RF_PARAMS = dict(n_estimators=100, min_samples_leaf=3, max_depth=10, class_weight="balanced", random_state=SEED, n_jobs=-1)


def load_clips(root, cache):
    if cache and os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        return list(z["iq"]), list(map(str, z["person"])), list(map(str, z["action"]))
    iq, person, action = [], [], []
    for pid in sorted(os.listdir(root)):
        for act in sorted(os.listdir(os.path.join(root, pid))):
            d = os.path.join(root, pid, act)
            for fn in sorted(os.listdir(d)):
                with open(os.path.join(d, fn), newline="") as fh:
                    rows = list(csv.DictReader(fh))
                iq.append(np.array([ast.literal_eval(r["data"]) for r in rows], dtype=np.float32))
                person.append(pid)
                action.append(act)
    return iq, person, action


def tree_to_dict(est):
    t = est.tree_
    value = t.value[:, 0, :]
    p_fall = value[:, 1] / np.maximum(value.sum(axis=1), 1e-12)
    return dict(feature=t.feature.tolist(), threshold=[float(v) for v in t.threshold],
                left=t.children_left.tolist(), right=t.children_right.tolist(),
                p_fall=[round(float(v), 6) for v in p_fall])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out_dir")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    iq, person, action = load_clips(args.root, args.cache)
    print(f"{len(iq)} clips; computing features with the application's code ...", flush=True)
    X = np.array([extract_features(a)[1] for a in iq])
    y = np.array([1 if a == "fall" else 0 for a in action])
    P = np.array(person)

    bals, rec, fpr = [], [], []
    pooled_pred = np.zeros(len(y), dtype=int)
    for held in sorted(set(person)):
        te, tr = np.where(P == held)[0], np.where(P != held)[0]
        clf = RandomForestClassifier(**RF_PARAMS).fit(X[tr], y[tr])
        p = clf.predict(X[te])
        pooled_pred[te] = p
        bals.append(balanced_accuracy_score(y[te], p))
        rec.append(float(((p == 1) & (y[te] == 1)).sum() / max(1, (y[te] == 1).sum())))
        fpr.append(float(((p == 1) & (y[te] == 0)).sum() / max(1, (y[te] == 0).sum())))
    evaluation = dict(
        protocol="leave-one-person-out over the 10 WiFall people, same hyper-parameters as the exported model",
        person_averaged_balanced_accuracy=round(float(np.mean(bals)), 3),
        person_averaged_fall_recall=round(float(np.mean(rec)), 3),
        person_averaged_false_alarm_rate=round(float(np.mean(fpr)), 3),
        per_person_balanced_accuracy_min=round(float(np.min(bals)), 3),
        per_person_balanced_accuracy_max=round(float(np.max(bals)), 3),
        chance_balanced_accuracy=0.5,
    )
    print("LOPO:", json.dumps(evaluation, indent=1), flush=True)

    final = RandomForestClassifier(**RF_PARAMS).fit(X, y)
    model = dict(
        model_type="random_forest_binary_fall_vs_not_fall",
        features=FEATURE_NAMES,
        classes={"0": "not_fall (jump, sit, stand, walk)", "1": "fall"},
        decision_threshold=0.5,
        score_meaning="uncalibrated forest score in 0..1; NOT the probability that a fall happened",
        window_packets=250,
        csi_format="52 subcarriers, (I,Q) int pairs, about 84 packets/s, ESP32-S3, 20 MHz, 2.4 GHz",
        trained_on="WiFall (Zhao et al., arXiv:2412.04783), all 10 people; one room, one transmitter, close range; "
                   "licence of the data is not stated, data not redistributed",
        n_training_clips=int(len(y)),
        hyperparameters={k: v for k, v in RF_PARAMS.items() if k != "n_jobs"},
        evaluation=evaluation,
        limitations=[
            "On a person the model has not seen it catches about 2 falls in 3 and falsely flags about 28% of non-falls.",
            "Measured only on WiFall (one room, one transmitter). Accuracy on other hardware or rooms is unknown.",
            "A fall can only ever be reported as a possible fall that needs human verification.",
        ],
        created=datetime.date.today().isoformat(),
        trees=[tree_to_dict(e) for e in final.estimators_],
    )
    out = os.path.join(BACKEND, "app", "ml", "wifall_rf_v2.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(model, fh, separators=(",", ":"))
    print(f"exported {out} ({os.path.getsize(out) / 1024:.0f} KB)", flush=True)

    # parity: application's numpy inference vs scikit-learn
    from app.services import fall_model
    fall_model._model, fall_model._load_error = None, None
    worst = 0.0
    for i in range(0, len(y), 7):
        mine = fall_model.fall_score(X[i])
        ref = float(final.predict_proba(X[i:i + 1])[0, 1])
        worst = max(worst, abs(mine - ref))
    print(f"parity with scikit-learn on {len(range(0, len(y), 7))} clips: worst absolute score difference {worst:.6f}")
    if worst > 1e-4:
        raise SystemExit("parity check FAILED")


if __name__ == "__main__":
    main()
