"""
WiFall improvement round (standalone; NOT part of the WiFi Sense application).

Pre-registered plan (fixed BEFORE looking at results):
  Primary metric : mean over the 10 held-out people of balanced accuracy for fall vs not-fall (person-averaged, so the
                   dominant person ID2 does not decide the headline). Secondary: pooled recall / false-alarm rate.
  Variants       : V0 baseline 24 features (reproduces round 1)
                   V1 = V0 without suspected shortcut features (absolute level, RSSI, packet count)
                   V2 = V1 + temporal and phase features
                   V3 = V2 + per-person normalisation using ALL of the person's UNLABELLED clips (optimistic, transductive)
                   V4 = V2 + per-person normalisation from only K=8 random UNLABELLED clips of the held-out person
                        (deployable: a short calibration period); evaluated on that person's remaining clips
  Judging        : a variant "helps" only if the person-averaged balanced accuracy rises by more than 0.03 AND it
                   improves a clear majority of the 10 people versus V1/V0 (sign count). Everything is reported.
  Labels         : used only as ground truth in this script (folder names). Normalisation never uses labels.
"""
import ast
import csv
import json
import os
import sys
import time
from collections import Counter

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT, OUT = sys.argv[1], sys.argv[2]
SEED, FS, K_CAL = 0, 84.0, 8
CLASSES = ["Jump", "fall", "sit", "stand", "walk"]
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ data (raw I/Q so phase is available)
def load_iq():
    cache = os.path.join(OUT, "clips_iq.npz")
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        return list(z["iq"]), list(z["rssi"]), list(map(str, z["person"])), list(map(str, z["action"]))
    iq, rssi, person, action = [], [], [], []
    for pid in sorted(os.listdir(ROOT)):
        for act in sorted(os.listdir(os.path.join(ROOT, pid))):
            d = os.path.join(ROOT, pid, act)
            for fn in sorted(os.listdir(d)):
                with open(os.path.join(d, fn), newline="") as fh:
                    rows = list(csv.DictReader(fh))
                iq.append(np.array([ast.literal_eval(r["data"]) for r in rows], dtype=np.float32))
                rssi.append(np.array([int(r["rssi"]) for r in rows], dtype=np.float32))
                person.append(pid)
                action.append(act)
    np.savez_compressed(cache, iq=np.array(iq, dtype=object), rssi=np.array(rssi, dtype=object),
                        person=np.array(person), action=np.array(action))
    return iq, rssi, person, action


def kurt(x):
    x = np.asarray(x, dtype=np.float64)
    s = x.std()
    return float(((x - x.mean()) ** 4).mean() / (s ** 4 + 1e-12)) if s > 0 else 0.0


def skew(x):
    x = np.asarray(x, dtype=np.float64)
    s = x.std()
    return float(((x - x.mean()) ** 3).mean() / (s ** 3 + 1e-12)) if s > 0 else 0.0


def autocorr(z, lag):
    z = z - z.mean()
    d = (z * z).sum() + 1e-12
    return float((z[:-lag] * z[lag:]).sum() / d)


def sanitized_phase(I, Q):
    """Phase per packet, unwrapped across subcarriers, with the linear trend (sampling/frequency offsets) removed."""
    ph = np.unwrap(np.arctan2(Q, I), axis=1)
    k = np.arange(ph.shape[1])
    out = np.empty_like(ph)
    for t in range(ph.shape[0]):
        a, b = np.polyfit(k, ph[t], 1)
        out[t] = ph[t] - (a * k + b)
    return out


V0_NAMES = []
EXTRA_NAMES = []


def feats(iq, r):
    I, Q = iq[:, 0::2], iq[:, 1::2]
    A = np.sqrt(I * I + Q * Q)
    n = A.shape[0]
    base, extra = {}, {}
    level = A.mean()
    sc_std = A.std(axis=0)
    base["motion_mean"] = sc_std.mean()
    base["motion_median"] = float(np.median(sc_std))
    base["motion_max"] = sc_std.max()
    base["motion_rel"] = sc_std.mean() / (level + 1e-6)
    m = A.mean(axis=1)
    z = (m - m.mean()) / (m.mean() + 1e-6)
    w, s = 20, 5
    wv = np.array([z[i:i + w].var() for i in range(0, n - w + 1, s)])
    base["burst_max"] = wv.max()
    base["burst_mean"] = wv.mean()
    base["burst_std"] = wv.std()
    base["burst_ratio"] = wv.max() / (np.median(wv) + 1e-9)
    base["burst_pos"] = float(np.argmax(wv)) / max(1, len(wv) - 1)
    base["burst_frac"] = float((wv > 1.5 * np.median(wv)).mean())
    d = np.abs(np.diff(A, axis=0))
    base["diff_mean"] = d.mean()
    base["diff_peak"] = d.mean(axis=1).max()
    base["diff_peak_rel"] = base["diff_peak"] / (d.mean() + 1e-9)
    spec = np.abs(np.fft.rfft(z * np.hanning(n))) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0 / FS)
    tot = spec[1:].sum() + 1e-12
    for lo, hi in [(0.5, 2), (2, 5), (5, 10), (10, 20), (20, 40)]:
        base[f"band_{lo}_{hi}"] = spec[(freqs >= lo) & (freqs < hi)].sum() / tot
    Ac = A - A.mean(axis=0)
    U, sv, Vt = np.linalg.svd(Ac, full_matrices=False)
    base["pc1_frac"] = (sv[0] ** 2) / ((sv ** 2).sum() + 1e-9)
    base["level"] = level
    base["level_cv"] = m.std() / (m.mean() + 1e-6)
    base["rssi_mean"] = r.mean()
    base["rssi_std"] = r.std()
    base["n_packets"] = n

    # ---- temporal-shape features (round 2)
    seg = np.array([x.var() for x in np.array_split(z, 5)])
    extra["seg_max_over_mean"] = seg.max() / (seg.mean() + 1e-12)
    p = seg / (seg.sum() + 1e-12)
    extra["seg_entropy"] = float(-(p * np.log(p + 1e-12)).sum())
    extra["seg_argmax"] = float(np.argmax(seg)) / 4.0
    extra["seg_first_vs_last"] = (seg[:2].mean() + 1e-12) / (seg[-2:].mean() + 1e-12)
    dz = np.diff(z)
    extra["dz_kurtosis"] = kurt(dz)
    extra["dz_skew"] = skew(dz)
    zs = np.convolve(z, np.ones(5) / 5, mode="same")
    extra["max_smoothed_slope"] = float(np.abs(np.diff(zs)).max())
    for lag in (5, 10, 20):
        extra[f"acf_{lag}"] = autocorr(z, lag)
    pc1 = U[:, 0] * sv[0]
    extra["pc1_kurtosis"] = kurt(pc1)
    extra["pc1_var_rel"] = float(pc1.var() / (A.var() * n + 1e-9))
    for name, sl in (("lo", slice(0, 17)), ("mid", slice(17, 35)), ("hi", slice(35, 52))):
        extra[f"grp_motion_{name}"] = A[:, sl].std(axis=0).mean() / (A[:, sl].mean() + 1e-6)
    # ---- phase features (round 2)
    ph = sanitized_phase(I, Q)
    extra["phase_std_mean"] = float(ph.std(axis=0).mean())
    extra["phase_diff_mean"] = float(np.abs(np.diff(ph, axis=0)).mean())
    pdm = np.abs(np.diff(ph, axis=0)).mean(axis=1)
    extra["phase_diff_peak_ratio"] = float(pdm.max() / (np.median(pdm) + 1e-9))
    return base, extra


SHORTCUT = {"level", "rssi_mean", "rssi_std", "n_packets"}


def build(iq, rssi):
    rows = [feats(a, r) for a, r in zip(iq, rssi)]
    base_names, extra_names = list(rows[0][0].keys()), list(rows[0][1].keys())
    names = base_names + extra_names
    X = np.array([[b[k] for k in base_names] + [e[k] for k in extra_names] for b, e in rows], dtype=np.float64)
    return X, names, base_names, extra_names


# ------------------------------------------------------------------ normalisation (no labels used)
def person_stats(X, idx):
    med = np.median(X[idx], axis=0)
    iqr = np.subtract(*np.percentile(X[idx], [75, 25], axis=0))
    return med, iqr + 1e-9


def normalise_by_person(X, persons, mode, rs, held=None, test_cal=None):
    """Returns normalised copy. mode 'full': each person's own stats from all their clips.
    mode 'k': each TRAINING person uses stats from K random clips; the held-out person uses ONLY test_cal clips."""
    Xn = X.copy()
    P = np.array(persons)
    for p in sorted(set(persons)):
        idx = np.where(P == p)[0]
        if mode == "full":
            med, iqr = person_stats(X, idx)
        else:
            if p == held:
                med, iqr = person_stats(X, test_cal)
            else:
                pick = rs.choice(idx, size=min(K_CAL, len(idx)), replace=False)
                med, iqr = person_stats(X, pick)
        Xn[idx] = (X[idx] - med) / iqr
    return Xn


# ------------------------------------------------------------------ evaluation
def make_model(name):
    if name == "LogisticRegression":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced"))
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced", random_state=SEED, n_jobs=-1)


def bin_metrics(y, p):
    tp = int(((y == 1) & (p == 1)).sum()); fn = int(((y == 1) & (p == 0)).sum())
    fp = int(((y == 0) & (p == 1)).sum()); tn = int(((y == 0) & (p == 0)).sum())
    return dict(tp=tp, fn=fn, fp=fp, tn=tn, recall=tp / max(1, tp + fn), precision=tp / max(1, tp + fp),
                fpr=fp / max(1, fp + tn), bal=balanced_accuracy_score(y, p) if len(set(y)) > 1 else float("nan"))


def lopo(X, y, persons, cols, model, norm):   # norm in {None, "full", "k"}
    P = np.array(persons)
    rs = np.random.default_rng(SEED)
    per, preds_all, idx_all, proba_all = {}, [], [], []
    for held in sorted(set(persons)):
        te_all = np.where(P == held)[0]
        tr = np.where(P != held)[0]
        if norm == "k":
            cal = rs.choice(te_all, size=K_CAL, replace=False)
            te = np.array([i for i in te_all if i not in set(cal)])      # evaluate on the remaining clips only
            Xn = normalise_by_person(X, persons, "k", np.random.default_rng(SEED + 1), held=held, test_cal=cal)
        elif norm == "full":
            te = te_all
            Xn = normalise_by_person(X, persons, "full", rs)
        else:
            te, Xn = te_all, X
        clf = make_model(model)
        clf.fit(Xn[tr][:, cols], y[tr])
        p = clf.predict(Xn[te][:, cols])
        pr = clf.predict_proba(Xn[te][:, cols])
        k1 = list(clf.classes_).index(1) if set(y) == {0, 1} else None
        per[held] = bin_metrics(y[te], p)
        per[held]["n"] = int(len(te))
        preds_all.append(p); idx_all.append(te)
        proba_all.append(pr[:, k1] if k1 is not None else pr.max(axis=1))
    idx = np.concatenate(idx_all)
    preds = np.concatenate(preds_all)
    pooled = bin_metrics(y[idx], preds)
    bals = np.array([per[h]["bal"] for h in sorted(per)])
    return dict(pooled=pooled, per_person=per, person_avg_bal=float(np.nanmean(bals)),
                person_avg_recall=float(np.mean([per[h]["recall"] for h in per])),
                person_avg_fpr=float(np.mean([per[h]["fpr"] for h in per])),
                bals=bals.tolist(), eval_idx=idx.tolist(), preds=preds.tolist(), proba=np.concatenate(proba_all).tolist())


def main():
    t0 = time.time()
    iq, rssi, persons, actions = load_iq()
    print(f"loaded {len(iq)} clips in {time.time() - t0:.0f}s", flush=True)
    X, names, base_names, extra_names = build(iq, rssi)
    print(f"features: {len(base_names)} base + {len(extra_names)} new = {X.shape[1]} ({time.time() - t0:.0f}s)", flush=True)
    y2 = np.array([1 if a == "fall" else 0 for a in actions])
    y5 = np.array([CLASSES.index(a) for a in actions])
    col = {n: i for i, n in enumerate(names)}
    V0 = [col[n] for n in base_names]
    V1 = [col[n] for n in base_names if n not in SHORTCUT]
    V2 = V1 + [col[n] for n in extra_names]
    variants = {"V0_baseline24": (V0, None), "V1_no_shortcuts": (V1, None), "V2_plus_temporal_phase": (V2, None),
                "V3_V2+person_norm_all_unlabelled": (V2, "full"), "V4_V2+person_norm_K8_calibration": (V2, "k")}
    res = dict(meta=dict(k_cal=K_CAL, seed=SEED, n_features=len(names), shortcut_dropped=sorted(SHORTCUT)), binary={})
    for vname, (cols, norm) in variants.items():
        res["binary"][vname] = {}
        for model in ("LogisticRegression", "RandomForest"):
            r = lopo(X, y2, persons, cols, model, norm)
            res["binary"][vname][model] = {k: v for k, v in r.items() if k not in ("eval_idx", "preds", "proba")}
            res["binary"][vname][model]["_raw"] = dict(eval_idx=r["eval_idx"], preds=r["preds"], proba=r["proba"])
            p = r["pooled"]
            print(f"  {vname:36s} {model:18s} person-avg bal={r['person_avg_bal']:.3f} "
                  f"(recall {r['person_avg_recall']:.2f}, fpr {r['person_avg_fpr']:.2f}) | pooled bal={p['bal']:.3f} "
                  f"recall={p['recall']:.2f} fpr={p['fpr']:.2f}", flush=True)
    # paired comparison versus V0 and V1 (per person)
    def paired(a, b):
        a, b = np.array(a), np.array(b)
        d = a - b
        return dict(mean_diff=float(np.nanmean(d)), improved=int((d > 0.0).sum()), worsened=int((d < 0.0).sum()),
                    tied=int((d == 0).sum()))
    res["paired"] = {}
    for model in ("LogisticRegression", "RandomForest"):
        b0 = res["binary"]["V0_baseline24"][model]["bals"]
        b1 = res["binary"]["V1_no_shortcuts"][model]["bals"]
        res["paired"][model] = {v: dict(vs_V0=paired(res["binary"][v][model]["bals"], b0),
                                        vs_V1=paired(res["binary"][v][model]["bals"], b1)) for v in variants}
    # 5-class with best-looking binary variant, shown for completeness (person-independent)
    best = max(((v, m) for v in variants for m in ("LogisticRegression", "RandomForest")),
               key=lambda t: res["binary"][t[0]][t[1]]["person_avg_bal"])
    cols, norm = variants[best[0]]
    P = np.array(persons)
    rs = np.random.default_rng(SEED)
    pred5 = np.zeros(len(y5), dtype=int)
    if norm != "k":
        for held in sorted(set(persons)):
            te = np.where(P == held)[0]; tr = np.where(P != held)[0]
            Xn = normalise_by_person(X, persons, "full", rs) if norm == "full" else X
            clf = make_model(best[1]); clf.fit(Xn[tr][:, cols], y5[tr]); pred5[te] = clf.predict(Xn[te][:, cols])
        cm = confusion_matrix(y5, pred5, labels=list(range(5)))
        res["five_class_best_variant"] = dict(variant=best[0], model=best[1],
                                              balanced_acc=float(balanced_accuracy_score(y5, pred5)),
                                              macro_f1=float(f1_score(y5, pred5, average="macro")),
                                              per_class_recall={CLASSES[i]: float(cm[i, i] / max(1, cm[i].sum())) for i in range(5)})
    else:
        res["five_class_best_variant"] = dict(variant=best[0], model=best[1], note="K-calibration variant evaluated on binary only")
    res["best_by_person_avg_bal"] = list(best)
    with open(os.path.join(OUT, "results2.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
