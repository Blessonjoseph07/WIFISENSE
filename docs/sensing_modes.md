# Sensing modes: demo, dataset replay, live hardware

WiFi Sense can show data from three sources. They are never mixed, and every screen says which one it is showing.

| Mode | Badge | What it is | Provenance stored | Status |
|---|---|---|---|---|
| Demo / preview | `DEMO` | Synthetic values that show how the system behaves before hardware exists | `simulated` | Implemented. Not a measurement. |
| Dataset replay | `DATASET REPLAY` | Real recorded CSI (WiFall) sent through the same authenticated ingest pipeline | `dataset` | Implemented and tested |
| Live hardware | `LIVE HARDWARE` | Packets from an authenticated ESP32-S3 device | `live` | Pipeline ready; **no real packet has been received yet** |

Provenance comes from the registered device (`allowed_source`), never from the packet. A client cannot claim a mode,
and ground-truth labels are rejected in packets.

## Pipeline

```
ESP32-S3 / replay tool -> POST /sensing/ingest (device token) -> RawCsiTelemetry
  -> 300-packet windows -> csi_features (38 features) -> random forest -> SensingEvent (same provenance)
  -> LIVE only: "Possible fall - verification required" alert; DATASET and DEMO never alert
```

- Only the format the model was trained on is analysed (52 subcarriers as 104 I/Q numbers); anything else is stored and skipped.
- DEMO devices never receive a model result.
- DATASET REPLAY never raises alerts or notifications.
- A fall flagged by the model is only ever a **possible** fall and always needs staff verification, whatever the score.

## What the detection can and cannot claim (graded like RuView's PROOF.md)

| Claim | Grade | Evidence |
|---|---|---|
| The application's pipeline reproduces the offline experiment exactly | **MEASURED** | Replaying the unseen person ID9 through the live API gave 16/16 falls flagged and 11/16 non-falls falsely flagged, identical to the offline fold. `test_dataset_replay.py` covers the rules with synthetic packets. |
| On a person never seen in training, fall vs not-fall balanced accuracy is about 0.69 (chance 0.50) | **MEASURED, with limits** | Leave-one-person-out on WiFall, `experiments/wifall`. Ten people; one room; one transmitter; the best of several configurations was reported in the improvement round (the deployed configuration is the one that was evaluated). |
| The model can be called a fall detector | **NOT SUPPORTED** | It catches about 2 falls in 3 and falsely flags about 28% of non-falls on unseen people. It can only raise a possible fall for a human to check. |
| Accuracy on the project's own ESP32-S3 boards and rooms | **HARDWARE-GATED / UNKNOWN** | Not measured. It requires real recordings and an evaluation. |
| "Confidence" values | **HEURISTIC** | Model scores are uncalibrated; above 0.9 the forest was right only about 71% of the time. The UI shows them as "uncalibrated". |
| "Signal quality" | **HEURISTIC** | 60% signal-to-noise margin and 40% packet completeness. It describes the radio link, not whether a detection is right (it read 100 for every replayed window). |
| Presence or "motion level" detection | **NOT IMPLEMENTED** | A plain variance score did not separate falls from jumping or standing on WiFall; presence needs an empty-room baseline, which the dataset does not contain. |

## Data

WiFall (Hugging Face `RS2002/WiFall`), citation Z. Zhao et al., *KNN-MMD*, arXiv:2412.04783. **No licence is stated** by
the authors; it is used for academic work only and is never stored in this repository. The deployed model is trained on
9 of 10 people; person ID9 is held out and is the person the replay tool replays by default.

## Running a replay

```bash
# 1. register a device with allowed_source "dataset" (organization admin); the token is shown once
# 2. download and extract WiFall yourself, then:
export WIFISENSE_API_BASE=http://localhost:8000
export WIFISENSE_DEVICE_TOKEN=...        # from step 1
export WIFISENSE_ADMIN_EMAIL=...         # an administrator of the device's organization
export WIFISENSE_ADMIN_PASSWORD=...
python tools/replay_wifall.py --data-dir /path/to/WiFall
```

Open **Sensing Monitor** in the app and choose DATASET REPLAY to see the windows, the recorded labels and the check of
recorded label versus the system's result.

## Not done yet

Presence detection with an empty-room baseline, real ESP32-S3 capture and measurement, per-room calibration,
and the wider removal of "Live" wording from older screens (Devices has been fixed; others remain).
