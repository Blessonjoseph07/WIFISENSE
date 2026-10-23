# Phase 2: learning this room (crowd level from Wi-Fi CSI)

## Why not a ready-made model
The fall model was trained on a public dataset in other rooms. Wi-Fi CSI depends on the room, the board placement and the people in it,
so a model like that flags constantly in a busy classroom. Instead of shipping a generic model, the system learns **your** room.

## How it works
1. In **Sensing Monitor > Live Hardware**, open **Learn this room**.
2. Record about 30 seconds each of: **Empty room**, **A few people**, **Busy**. Each press of *Record 30 s* saves the last 30 seconds
   of the board's packets under that label. Two situations are enough to start; all three is better; two recordings of each is best.
3. Press **Train the model**. It learns from the first 70% of every recording and is tested on the last 30%, which it never saw.
   The result card shows the held-out accuracy, what simply guessing would score, and a confusion matrix.
4. The live estimate (Empty / A few people / Busy, with a confidence) follows the board's signal. If the model failed its own test it
   says **NOT reliable** and the estimate is labelled a guess.

## What the model is
Multinomial logistic regression (plain numpy) on four features of every 50-packet block (about half a second at the radio's rate): amplitude
variation, its 90th percentile across subcarriers, RSSI spread and short-term motion energy. The estimate averages the last 10 blocks.
The data stays in the database (the board's calibration record); nothing leaves the system.

## Honest limits
- It estimates a **crowd level** from one pair of boards. It does not count, locate or identify people.
- It is valid for the board placement and room conditions it was recorded in. Move the boards or change the room: record again.
- The held-out accuracy comes from the same day and the same recordings. It is an optimistic number; check it again on another day.
- Reliable means: at least 6 held-out blocks per situation, at least 75% accuracy, and clearly better than guessing.

## API
`GET /sensing/devices/{id}/occupancy`, `POST .../occupancy/capture {label, seconds, from_packet_id?}`, `POST .../occupancy/train`,
`DELETE .../occupancy` (recording, training and reset need a system administrator or facility manager; every change is audited).
