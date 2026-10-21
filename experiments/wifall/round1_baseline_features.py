"""
WiFall detection experiment (standalone; NOT part of the WiFi Sense application).

Question: how well can simple, explainable features from raw ESP32-S3 CSI clips tell a FALL from other actions,
when the model is tested on a person it has never seen?

Data: WiFall (Hugging Face RS2002/WiFall), 928 clips of ~3 s (~250 packets, 52 subcarriers), 10 people, 5 actions.
Labels come only from the folder name and are used ONLY as ground truth for training/scoring in this script.

Evaluation rules
  * leave-one-person-out (LOPO): every person is held out once; the model never sees that person while training
  * results are reported per person and pooled; the majority-class baseline and a one-feature threshold baseline are
    shown next to the models
  * a deliberately LEAKY random-clip split is shown only to demonstrate how misleading it is
  * a second training regime caps the dominant person (ID2 has 69% of all clips) so one person cannot dominate training
"""
import ast
import csv
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = sys.argv[1]            # path to the extracted WiFall folder
OUT = sys.argv[2]             # output directory
SEED = 0
FS = 84.0                     # median packet rate measured on the data (Hz); only used for spectral band edges
CLASSES = ["Jump", "fall", "sit", "stand", "walk"]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(SEED)


# ----------------------------------------------------------------------------- load
def load_clips():
    cache = os.path.join(OUT, "clips.npz")
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        return list(z["amps"]), list(z["rssi"]), list(z["person"]), list(z["action"])
    amps, rssi, person, action = [], [], [], []
    for pid in sorted(os.listdir(ROOT)):
        for act in sorted(os.listdir(os.path.join(ROOT, pid))):
            d = os.path.join(ROOT, pid, act)
            for fn in sorted(os.listdir(d)):
                with open(os.path.join(d, fn), newline="") as fh:
                    rows = list(csv.DictReader(fh))
                a = np.array([ast.literal_eval(r["data"]) for r in rows], dtype=np.float32)   # (n, 104)
                i, q = a[:, 0::2], a[:, 1::2]
                amps.append(np.sqrt(i * i + q * q))                                          # (n, 52)
                rssi.append(np.array([int(r["rssi"]) for r in rows], dtype=np.float32))
                person.append(pid)
                action.append(act)
    np.savez_compressed(cache, amps=np.array(amps, dtype=object), rssi=np.array(rssi, dtype=object),
                        person=np.array(person), action=np.array(action))
    return amps, rssi, person, action


# ----------------------------------------------------------------------------- features
FEATURE_NAMES = []


def clip_features(A, r):
    """Explainable features from one clip. A: (n_packets, 52) amplitude, r: rssi per packet."""
    n = A.shape[0]
    f = {}
    level = A.mean()
    sc_std = A.std(axis=0)
    f["motion_mean"] = sc_std.mean()
    f["motion_median"] = float(np.median(sc_std))
    f["motion_max"] = sc_std.max()
    f["motion_rel"] = sc_std.mean() / (level + 1e-6)                   # scale-free version

    m = A.mean(axis=1)                                                 # mean amplitude per packet
    z = (m - m.mean()) / (m.mean() + 1e-6)
    w, s = 20, 5
    wv = np.array([z[i:i + w].var() for i in range(0, n - w + 1, s)])
    f["burst_max"] = wv.max()
    f["burst_mean"] = wv.mean()
    f["burst_std"] = wv.std()
    f["burst_ratio"] = wv.max() / (np.median(wv) + 1e-9)
    f["burst_pos"] = float(np.argmax(wv)) / max(1, len(wv) - 1)         # where in the clip the peak is
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
    sv = np.linalg.svd(Ac, compute_uv=False)
    f["pc1_frac"] = (sv[0] ** 2) / ((sv ** 2).sum() + 1e-9)             # how coherent the variation is across subcarriers
    f["level"] = level
    f["level_cv"] = m.std() / (m.mean() + 1e-6)
    f["rssi_mean"] = r.mean()
    f["rssi_std"] = r.std()
    f["n_packets"] = n
    return f


def build_matrix(amps, rssi):
    rows = [clip_features(a, r) for a, r in zip(amps, rssi)]
    names = list(rows[0].keys())
    FEATURE_NAMES[:] = names
    return np.array([[row[k] for k in names] for row in rows], dtype=np.float64)


# ----------------------------------------------------------------------------- helpers
def binary_metrics(y_true, y_pred, proba=None):
    """positive class = fall (1)."""
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    recall = tp / max(1, tp + fn)
    precision = tp / max(1, tp + fp)
    fpr = fp / max(1, fp + tn)
    return dict(tp=tp, fn=fn, fp=fp, tn=tn, recall=recall, precision=precision, fpr=fpr,
                balanced_acc=balanced_accuracy_score(y_true, y_pred))


def models():
    return {
        "RandomForest": lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced",
                                                       random_state=SEED, n_jobs=-1),
        "LogisticRegression": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
        "OneFeatureThreshold(motion_mean)": None,   # handled separately
    }


def cap_training(idx, persons, y, cap_per_person_class, rs):
    """Keep at most `cap` clips per (person, class) so one person cannot dominate training."""
    keep = []
    groups = defaultdict(list)
    for i in idx:
        groups[(persons[i], y[i])].append(i)
    for key, ids in groups.items():
        ids = list(ids)
        rs.shuffle(ids)
        keep.extend(ids[:cap_per_person_class])
    return np.array(sorted(keep))


def lopo(X, y, persons, task, regime, model_name):
    """Leave-one-person-out. Returns pooled predictions and per-person metrics."""
    rs = np.random.default_rng(SEED)
    P = np.array(persons)
    preds = np.zeros(len(y), dtype=int)
    proba = np.zeros(len(y), dtype=float)       # P(fall) for binary, max-prob for multiclass
    per_person = {}
    for held in sorted(set(persons)):
        te = np.where(P == held)[0]
        tr = np.where(P != held)[0]
        if regime == "capped":
            tr = cap_training(tr, persons, y, 8, rs)
        if model_name == "OneFeatureThreshold(motion_mean)":
            clf = DecisionTreeClassifier(max_depth=1, class_weight="balanced", random_state=SEED)
            Xtr, Xte = X[tr][:, [FEATURE_NAMES.index("motion_mean")]], X[te][:, [FEATURE_NAMES.index("motion_mean")]]
        else:
            clf = models()[model_name]()
            Xtr, Xte = X[tr], X[te]
        clf.fit(Xtr, y[tr])
        p = clf.predict(Xte)
        pr = clf.predict_proba(Xte)
        preds[te] = p
        if task == "binary":
            col = list(clf.classes_).index(1)
            proba[te] = pr[:, col]
        else:
            proba[te] = pr.max(axis=1)
        if task == "binary":
            per_person[held] = binary_metrics(y[te], p)
            per_person[held]["n"] = int(len(te))
            per_person[held]["n_fall"] = int((y[te] == 1).sum())
        else:
            per_person[held] = dict(balanced_acc=balanced_accuracy_score(y[te], p),
                                    macro_f1=f1_score(y[te], p, average="macro"), n=int(len(te)))
    return preds, proba, per_person


def majority_baseline(y, persons):
    P = np.array(persons)
    out = {}
    for held in sorted(set(persons)):
        tr, te = np.where(P != held)[0], np.where(P == held)[0]
        maj = Counter(y[tr]).most_common(1)[0][0]
        out[held] = (np.full(len(te), maj), te)
    return out


def summarize_per_person(per_person, keys):
    out = {}
    for k in keys:
        vals = [v[k] for v in per_person.values()]
        out[k] = dict(mean=float(np.mean(vals)), min=float(np.min(vals)), max=float(np.max(vals)))
    return out


def calibration(y_true, y_pred, conf, bins=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01)):
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf >= lo) & (conf < hi)
        if m.sum():
            rows.append(dict(bin=f"{lo:.1f}-{min(hi, 1.0):.1f}", n=int(m.sum()),
                             mean_confidence=float(conf[m].mean()), accuracy=float((y_true[m] == y_pred[m]).mean())))
    ece = sum(r["n"] * abs(r["mean_confidence"] - r["accuracy"]) for r in rows) / max(1, len(y_true))
    return rows, float(ece)


# ----------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    print("loading clips ...", flush=True)
    amps, rssi, persons, actions = load_clips()
    persons = list(map(str, persons))
    actions = list(map(str, actions))
    print(f"  {len(amps)} clips loaded in {time.time() - t0:.0f}s", flush=True)

    X = build_matrix(amps, rssi)
    y5 = np.array([CLASSES.index(a) for a in actions])
    y2 = np.array([1 if a == "fall" else 0 for a in actions])
    print(f"  feature matrix {X.shape}; fall share {y2.mean():.2f}", flush=True)

    res = dict(meta=dict(n_clips=len(amps), n_features=X.shape[1], features=FEATURE_NAMES, seed=SEED,
                         clips_per_person=dict(Counter(persons)), clips_per_action=dict(Counter(actions)),
                         fall_share=float(y2.mean())))

    # ---- binary: fall vs not-fall
    res["binary"] = {}
    for regime in ("full", "capped"):
        res["binary"][regime] = {}
        for name in ("OneFeatureThreshold(motion_mean)", "LogisticRegression", "RandomForest"):
            preds, proba, per = lopo(X, y2, persons, "binary", regime, name)
            pooled = binary_metrics(y2, preds)
            res["binary"][regime][name] = dict(
                pooled=pooled,
                per_person_summary=summarize_per_person(per, ["recall", "precision", "fpr", "balanced_acc"]),
                per_person={k: {kk: (float(vv) if isinstance(vv, (float, np.floating)) else vv) for kk, vv in v.items()}
                            for k, v in per.items()},
            )
            if name == "RandomForest":
                bins, ece = calibration(y2, preds, np.where(preds == 1, proba, 1 - proba))
                res["binary"][regime][name]["calibration"] = dict(bins=bins, ece=ece)
            print(f"  binary/{regime}/{name}: recall={pooled['recall']:.2f} precision={pooled['precision']:.2f} "
                  f"fpr={pooled['fpr']:.2f} bal_acc={pooled['balanced_acc']:.2f}", flush=True)
    # majority baseline
    mb = majority_baseline(y2, persons)
    pred_all = np.zeros(len(y2), dtype=int)
    for held, (p, te) in mb.items():
        pred_all[te] = p
    res["binary"]["majority_baseline"] = binary_metrics(y2, pred_all)

    # ---- 5-class
    res["five_class"] = {}
    for regime in ("full", "capped"):
        res["five_class"][regime] = {}
        for name in ("LogisticRegression", "RandomForest"):
            preds, proba, per = lopo(X, y5, persons, "multi", regime, name)
            cm = confusion_matrix(y5, preds, labels=list(range(5)))
            res["five_class"][regime][name] = dict(
                pooled_balanced_acc=float(balanced_accuracy_score(y5, preds)),
                pooled_macro_f1=float(f1_score(y5, preds, average="macro")),
                per_class_recall={CLASSES[i]: float(cm[i, i] / max(1, cm[i].sum())) for i in range(5)},
                confusion_matrix=dict(labels=CLASSES, matrix=cm.tolist()),
                per_person_summary=summarize_per_person(per, ["balanced_acc", "macro_f1"]),
            )
            print(f"  5class/{regime}/{name}: balanced_acc={res['five_class'][regime][name]['pooled_balanced_acc']:.2f} "
                  f"macro_f1={res['five_class'][regime][name]['pooled_macro_f1']:.2f}", flush=True)
    maj5 = Counter(y5).most_common(1)[0][1] / len(y5)
    res["five_class"]["majority_accuracy"] = float(maj5)
    res["five_class"]["chance_balanced_acc"] = 0.2

    # ---- deliberately leaky random split (same people in train and test) -> shows inflation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    leaky_pred = np.zeros(len(y2), dtype=int)
    leaky5 = np.zeros(len(y5), dtype=int)
    for tr, te in skf.split(X, y5):
        m = models()["RandomForest"]()
        m.fit(X[tr], y2[tr]); leaky_pred[te] = m.predict(X[te])
        m5 = models()["RandomForest"]()
        m5.fit(X[tr], y5[tr]); leaky5[te] = m5.predict(X[te])
    res["leaky_random_split"] = dict(binary=binary_metrics(y2, leaky_pred),
                                     five_class_balanced_acc=float(balanced_accuracy_score(y5, leaky5)),
                                     note="Same people appear in train and test. Shown only to demonstrate inflation.")
    print(f"  LEAKY random split (do not trust): fall recall={res['leaky_random_split']['binary']['recall']:.2f}, "
          f"5-class bal_acc={res['leaky_random_split']['five_class_balanced_acc']:.2f}", flush=True)

    # ---- which features matter (RandomForest on everything, only for interpretation)
    rf = models()["RandomForest"]()
    rf.fit(X, y2)
    imp = sorted(zip(FEATURE_NAMES, rf.feature_importances_), key=lambda t: -t[1])[:8]
    res["top_features_fall_vs_not"] = [(k, float(v)) for k, v in imp]

    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"done in {time.time() - t0:.0f}s; results written to {OUT}", flush=True)


if __name__ == "__main__":
    main()
