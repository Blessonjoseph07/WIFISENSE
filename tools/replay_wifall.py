#!/usr/bin/env python3
"""
Replay recorded WiFall CSI through the authenticated /sensing/ingest pipeline (DATASET REPLAY).

This is a tool for administrators. It does NOT make anything live: the target device must be registered with
allowed_source = "dataset", so the server stores every packet with provenance `dataset` and the UI shows
DATASET REPLAY. Ground-truth labels never travel with the packets; they are recorded afterwards through the
admin-only /sensing/replay/evaluations endpoint so the detector's own output can be compared with them.

By default only the person the deployed model never saw during training is replayed (the model file says which one),
so the result is an honest test of an unseen person. Replaying people the model was trained on is possible with
--include-training-people but is labelled as such and proves nothing about accuracy.

Environment (credentials are never taken from the command line, so they stay out of shell history):
  WIFISENSE_API_BASE         default http://localhost:8000
  WIFISENSE_DEVICE_TOKEN     token of a device registered with allowed_source "dataset" (shown once at registration)
  WIFISENSE_ADMIN_EMAIL      an organization administrator (or system administrator) of that device's organization
  WIFISENSE_ADMIN_PASSWORD

Usage
  python replay_wifall.py --data-dir /path/to/WiFall [--limit 32] [--pace 0]

Data: WiFall, https://huggingface.co/datasets/RS2002/WiFall (licence not stated; do not redistribute).
Citation: Z. Zhao et al., KNN-MMD, arXiv:2412.04783.
"""
import argparse
import ast
import csv
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

BATCH = 50   # packets per request; 100 packets would approach the server's 64 KB request limit


def call(base, path, method="GET", data=None, jwt=None, device_token=None):
    req = urllib.request.Request(base + path, method=method,
                                 data=json.dumps(data).encode() if data is not None else None)
    req.add_header("Content-Type", "application/json")
    if jwt:
        req.add_header("Authorization", f"Bearer {jwt}")
    if device_token:
        req.add_header("X-Device-Token", device_token)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, body


def to_utc_iso(stamp):
    """WiFall timestamps are UTC+8 wall-clock strings like 2023-11-12 21:21:03.546."""
    dt = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S.%f") - datetime.timedelta(hours=8)
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat()


def clip_packets(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    pkts = []
    for r in rows:
        pkts.append({
            "sequence_number": int(r["seq"]),
            "timestamp": to_utc_iso(r["timestamp"]),
            "rssi": int(r["rssi"]),
            "noise_floor": int(r["noise_floor"]),
            "subcarrier_count": 52,
            "bandwidth_mhz": 20,
            "channel": int(r["channel_primary"]),
            "csi_data": {"iq": ast.literal_eval(r["data"])},     # the recorded label ("taget") is deliberately NOT sent
        })
    return pkts


def need(var):
    value = os.environ.get(var)
    if not value:
        sys.exit(f"Set {var} (see the docstring of this file).")
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, help="the extracted WiFall folder (contains ID0 ... ID9)")
    ap.add_argument("--limit", type=int, default=0, help="replay at most this many clips (0 = all of the chosen person)")
    ap.add_argument("--pace", type=float, default=0.0, help="seconds to wait between clips")
    ap.add_argument("--include-training-people", action="store_true",
                    help="also replay people the model was trained on (labelled as such; proves nothing about accuracy)")
    args = ap.parse_args()

    base = os.environ.get("WIFISENSE_API_BASE", "http://localhost:8000").rstrip("/")
    token = need("WIFISENSE_DEVICE_TOKEN")
    status, auth = call(base, "/auth/login", "POST", {"email": need("WIFISENSE_ADMIN_EMAIL"),
                                                       "password": need("WIFISENSE_ADMIN_PASSWORD")})
    if status != 200:
        sys.exit(f"Login failed: {status} {auth}")
    jwt = auth["access_token"]

    status, info = call(base, "/sensing/model-info", jwt=jwt)
    if status != 200 or not info.get("available"):
        sys.exit(f"Detection model unavailable: {info}")
    held = info.get("held_out_person")
    print(f"Model: {info['model_type']}; held-out person: {held}; "
          f"person-independent balanced accuracy (leave-one-person-out): "
          f"{info['evaluation']['person_averaged_balanced_accuracy']}")
    if not held:
        sys.exit("The model file does not name a held-out person; refusing to present a replay as an unseen-person test.")

    people = [held] + ([p for p in sorted(os.listdir(args.data_dir)) if p != held and p.startswith("ID")]
                       if args.include_training_people else [])
    clips = []
    for pid in people:
        for action in sorted(os.listdir(os.path.join(args.data_dir, pid))):
            d = os.path.join(args.data_dir, pid, action)
            for fn in sorted(os.listdir(d)):
                clips.append((pid, action, os.path.join(d, fn)))
    if args.limit:
        clips = clips[:args.limit]
    print(f"Replaying {len(clips)} clips through {base}/sensing/ingest as DATASET REPLAY ...")

    tp = fn = fp = tn = 0
    per_label = {}
    for n, (pid, action, path) in enumerate(clips, 1):
        pkts = clip_packets(path)
        detections = []
        for i in range(0, len(pkts), BATCH):
            status, res = call(base, "/sensing/ingest", "POST", {"packets": pkts[i:i + BATCH]}, device_token=token)
            if status != 201:
                sys.exit(f"Ingest failed ({status}): {res}")
            detections += res["detections"]
        status, flushed = call(base, "/sensing/detect", "POST", {}, device_token=token)
        if status != 200:
            sys.exit(f"Detect failed ({status}): {flushed}")
        detections += flushed["detections"]
        if len(detections) != 1:
            print(f"  [{n}/{len(clips)}] {pid}/{action}: expected one detection window, got {len(detections)} "
                  f"({flushed.get('note')}); not counted")
            continue
        d = detections[0]
        dataset = "WiFall (held-out person, unseen by the model)" if pid == held else "WiFall (person IN training set: plumbing demo only)"
        status, res = call(base, "/sensing/replay/evaluations", "POST",
                           {"event_id": d["event_id"], "recorded_label": action, "dataset_name": dataset}, jwt=jwt)
        if status != 201:
            sys.exit(f"Recording the label failed ({status}): {res}")
        actual_fall, flagged = action == "fall", bool(d["fall_suspected"])
        if pid == held:
            tp += actual_fall and flagged
            fn += actual_fall and not flagged
            fp += (not actual_fall) and flagged
            tn += (not actual_fall) and not flagged
            row = per_label.setdefault(action, [0, 0])
            row[0] += 1
            row[1] += int(flagged)
        print(f"  [{n}/{len(clips)}] {pid}/{action:5s} -> {d['activity']:15s} score {d['fall_score']:.3f}  "
              f"signal quality {d['signal_quality']}  ({d['window_packets']} packets)", flush=True)
        if args.pace:
            time.sleep(args.pace)

    print("\nUnseen-person result (recorded labels compared with the detector's own output):")
    print(f"  recorded falls flagged as possible fall : {tp} of {tp + fn}")
    print(f"  non-falls falsely flagged                : {fp} of {fp + tn}")
    for label, (total, flagged) in sorted(per_label.items()):
        print(f"    {label:6s}: {flagged} of {total} flagged")
    print("This is REPLAYED, RECORDED data from one person in one room. It is not live sensing, and with this few "
          "clips the numbers are noisy.")
    status, summ = call(base, "/sensing/replay/summary", jwt=jwt)
    if status == 200:
        print("\nServer-side summary:", json.dumps({k: v for k, v in summ.items() if k != 'statement'}))


if __name__ == "__main__":
    main()
