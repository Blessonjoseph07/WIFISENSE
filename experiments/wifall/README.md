# WiFall experiments (evidence, not application code)

These scripts measure how well simple, explainable features from raw ESP32-S3 CSI can tell a **fall** from other
actions **on a person the model has never seen**. They are kept in the repository as evidence for the project report.
**No dataset files are stored here.**

## The data

WiFall: 928 clips of about 3 seconds (about 250 packets at about 84 Hz, 52 complex subcarriers), 10 people,
5 actions (fall, jump, sit, stand, walk), recorded with ESP32-S3 devices in one meeting room.

- Source: <https://huggingface.co/datasets/RS2002/WiFall> (file `WiFall.zip`, 29,360,158 bytes)
- Citation: Z. Zhao et al., *KNN-MMD: Cross Domain Wireless Sensing via Local Distribution Alignment*, arXiv:2412.04783
- **Licence: not stated** by the dataset card or the authors' code repository. It is used here for academic work only.
  Do not commit or redistribute the data; download it yourself.
- Facts measured on the real files: person ID2 holds 640 of the 928 clips (the others 32 each); falls are half of all
  clips; one clip has a timestamp counter that runs backwards; RSSI is strong (median -29 dBm) and the noise floor is
  almost always -99 dBm; one channel, one transmitter.

## Running

```bash
# 1. download WiFall.zip yourself and extract it so that ROOT/ID0 ... ROOT/ID9 exist
# 2. needs numpy and scikit-learn (not part of the application's requirements)
python round1_baseline_features.py            /path/to/WiFall  ./out_round1
python round2_temporal_phase_normalisation.py /path/to/WiFall  ./out_round2
```

Both scripts are deterministic (seed 0). Each takes about 1.5 minutes after the first load.

## Evaluation rules

- **Leave-one-person-out**: every person is held out once and never seen in training.
- The headline number is the **person-averaged** balanced accuracy (0.50 is chance). A pooled number is dominated by
  person ID2 and is only secondary.
- Baselines (always-"not fall", a one-feature threshold) are reported next to the models.
- A deliberately **leaky** random split is shown only to demonstrate how misleading easy evaluation is.
- Labels are the folder names and are used only as ground truth inside these scripts.

## Results (copied from `results_round1.json` and `results_round2.json`)

Fall vs not-fall, person-independent, **person-averaged balanced accuracy**:

| Variant | Logistic regression | Random forest |
|---|---|---|
| V0 round-1 baseline, 24 features | 0.655 | 0.644 |
| V1 without suspected shortcut features (RSSI, absolute level, packet count) | 0.664 | 0.645 |
| V2 V1 plus temporal-shape and phase features | 0.661 | **0.689** |
| V3 V2 plus per-person normalisation using all of the person's unlabelled clips (optimistic) | 0.714 | 0.711 |
| V4 V2 plus per-person normalisation from only 8 unlabelled clips | 0.666 | 0.695 |

- Per-person balanced accuracy ranges from about 0.46 to 0.87 depending on the variant: the model is very
  person-dependent.
- Five actions, person-independent: balanced accuracy 0.37 (round 1) and 0.455 (best case of round 2); chance is 0.20.
- Leaky random split, for contrast only: 0.86 balanced accuracy for fall vs not-fall.
- Random-forest scores are roughly calibrated at mid range but overconfident above 0.9 (accuracy about 0.71).

## What may and may not be claimed

- Falls are **never** "detected" by this model. At best the output is **"Possible fall - verification required"**.
- The deployable model is the **random forest on the V2 features without per-person calibration**
  (person-averaged balanced accuracy 0.688 with the exported 100-tree configuration: it catches about 2 falls in 3 and
  falsely flags about 28% of non-falls).
- The best figure (0.714) is optimistic: ten configurations were tried and the best is quoted, and V3 needs far more
  of a person's data than a short calibration (V4 shows an 8-clip calibration adds nothing beyond V2).
- Everything was measured on one room, one transmitter and close range. Accuracy on other hardware and rooms is
  **unknown** until it is measured there.
- Ten people is a small sample: differences of about 0.03-0.05 are close to noise.
