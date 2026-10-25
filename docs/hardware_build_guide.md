# Wi-Fi Sense hardware build guide (ESP32-S3 + OLED)

A step-by-step build of the two sensing nodes, from bare boards to a trained room model.

```
 TX node (power bank or charger)                RX node (USB to the PC)
 ┌───────────────────────────┐   Wi-Fi frames   ┌───────────────────────────┐   USB serial   ┌──────────────┐
 │ ESP32-S3-WROOM-1U + antenna│ ───────────────> │ ESP32-S3-WROOM-1U + antenna│ ─────────────> │ csi_serial_  │ ──HTTP──> API ──> dashboard
 │ OLED: "SENDING 100/s"      │  ch 11, 6 Mbps   │ OLED: CSI rate + room state│ <───────────── │ bridge.py    │ <─state──┘
 └───────────────────────────┘                  └───────────────────────────┘   WS_STATE line └──────────────┘
```

**Parts per node:** 1 × ESP32-S3-WROOM-1U-N16R8 board (headers soldered), 1 × U.FL/IPEX antenna, 1 × 0.96-inch SSD1306 I²C
OLED (128×64), 1 × breadboard, 4 jumper wires, 1 × USB-C data cable.

---

## 0. Heads-up: power and safety (read before wiring)

| Topic | What to do | Why |
|---|---|---|
| **Antenna first** | Click the U.FL antenna onto the module **before** plugging in USB, and never run the TX board without it. | The 1U module has no PCB antenna. Transmitting into an open connector reflects the RF power back into the chip and gives a weak, unstable signal. |
| **U.FL connector** | Press it straight down until it clicks. Remove it by lifting straight up (a U.FL tool or a fingernail under the collar), never by pulling the cable. | The connector is rated for only about 30 connections and breaks easily if pulled at an angle. |
| **OLED on 3V3, not 5V** | Wire the OLED's **VCC to the board's 3V3 pin**. | The OLED module's pull-up resistors connect SDA/SCL to its VCC. With 5 V, the data lines sit at 5 V, and the ESP32-S3's GPIOs are **not 5 V tolerant**. |
| **Check the OLED pin order** | Read the labels printed on *your* OLED. Some are `GND VCC SCL SDA`, others `VCC GND SCL SDA`. | Swapping VCC and GND destroys the display in seconds. |
| **Current budget** | Per node: ESP32-S3 with Wi-Fi ≈ 100–150 mA average, **peaks ≈ 350 mA** while transmitting; OLED 10–25 mA. A USB 2.0 port (500 mA) or any phone charger is enough. | The board's own 3.3 V regulator feeds the OLED, so there is no separate supply. |
| **Power bank on the TX** | If the TX board **switches off after 10–60 seconds**, the power bank is cutting out at low load. Use a phone wall charger instead, or a bank with an "always on / low-current" mode. | Many power banks turn off below about 50–100 mA. The TX usually draws more than that, but some banks are stricter. |
| **One power source per board** | Power each board from **one** USB-C cable only. Do not also feed the 5V or 3V3 pins from another supply. | Two supplies fighting each other can damage the regulator or the PC's USB port. |
| **Which USB-C port** | Many ESP32-S3 boards have two ports: **"COM"/"UART"** (through a USB-UART chip) and **"USB"** (native). For the **RX**, use **COM/UART**: that is the port the board reads the bridge's display line from. Either port works for the TX. | Both ports carry the CSI output, but only the UART port carries the state line back to the OLED. |
| **Static** | Touch a grounded metal object before handling the boards; hold them by the edges. | |

---

## 1. Wire the OLED on the breadboard (same for both boards)

The ESP32-S3 dev board is wide. On a standard breadboard it covers almost all the holes, so place it **across the centre
gap with one row of free holes on at least one side**, or put two breadboards side by side and let the board bridge them.

| OLED pin | Wire colour (suggested) | ESP32-S3 board pin | Notes |
|---|---|---|---|
| **GND** | black | **GND** | any GND pin |
| **VCC** | red | **3V3** | **not 5V** (see section 0) |
| **SCL** | yellow | **GPIO 9** (labelled `9` or `IO9`) | I²C clock |
| **SDA** | blue | **GPIO 8** (labelled `8` or `IO8`) | I²C data |

```
          ESP32-S3 board (top view, USB-C at the bottom)            0.96" OLED
   ┌────────────────────────────────────────────┐              ┌──────────────────┐
   │ 3V3 ●─────────────────────── red ───────────┼──────────────┤ VCC              │
   │     ●                                       │              │                  │
   │  …                                          │              │   128 x 64       │
   │ IO8 ●─────────────────────── blue ──────────┼──────────────┤ SDA              │
   │  …                                          │              │                  │
   │ IO9 ●─────────────────────── yellow ────────┼──────────────┤ SCL              │
   │  …                                          │              │                  │
   │ GND ●─────────────────────── black ─────────┼──────────────┤ GND              │
   └───────────────[USB-C COM]──[USB-C USB]──────┘              └──────────────────┘
```

On the common ESP32-S3-DevKitC-1 layout, `3V3` is pin 1 of the left header, `IO8` pin 12, `IO9` pin 15 and `GND` the
last pin. Clone boards differ, so **follow the labels printed on your board**, not the position.

**Pins you must not use** for anything on the N16R8 module: GPIO 26–37 (flash and octal PSRAM), 19/20 (USB), 43/44
(the console UART) and 0/3/45/46 (strapping pins: these can stop the board from booting). GPIO 8/9 are free and are the
firmware defaults. To use other pins: `idf.py menuconfig` → *Wi-Fi Sense OLED display*.

**Check before power:** VCC goes to 3V3, GND to GND, and no wire sits on a strapping pin. The display is optional: without
it (or with a loose wire) the board logs `no SSD1306 at 0x3C/0x3D ... running without a display` and keeps sensing.

---

## 2. Attach the antennas

1. Click a U.FL antenna onto each module (section 0).
2. Stand both antennas **vertically and parallel** (the same orientation on both boards).
3. Keep them away from metal (laptop lids, metal shelves, the breadboard's metal backing if it has one).

---

## 3. Flash the firmware

ESP-IDF v6.1 is installed at `E:\esp\v6.1\esp-idf`. Open the **ESP-IDF 6.1 PowerShell** from the Start menu, or in any
PowerShell run `. C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1`.

1. Plug in **one board at a time** and note its COM port (Device Manager → *Ports (COM & LPT)*, or `mode`).
2. Build and flash:

```powershell
cd D:\Wifisense\firmware\csi_send ; idf.py build ; idf.py -p COM5 flash      # TX board (use its port)
cd D:\Wifisense\firmware\csi_recv ; idf.py build ; idf.py -p COM4 flash      # RX board (use its port)
```

If flashing cannot connect, hold **BOOT**, tap **RESET**, release **BOOT**, and run the flash command again.

3. What the OLEDs should show after a reset:

| Board | OLED |
|---|---|
| TX | `WIFI SENSE TX CH11`, big **SENDING**, `rate ~100/s`, `send errors 0` |
| RX (TX on, bridge not running) | `CSI 80-100/s RSSI -40…-60`, `WAITING FOR PC`, `start the bridge` |

`CSI 0/s` with `no frames from TX` means the TX is off, out of range or on another channel. A rising `dropped` count means
the frames are arriving in the wrong format (see `firmware/README.md`).

---

## 4. Place the boards

The model learns **this exact placement**. If a board is moved, the baseline and the trained model no longer fit, so record
again.

* 2–4 m apart, about 1 m above the floor (bed or chair height), with the area you care about (bed, chair, walkway) **between** them.
* Fix them in place (tape or a stand) so they cannot slide or rotate.
* TX: power bank or charger. RX: USB to the PC (COM/UART port).
* Keep fans and moving curtains out of the line between the boards when possible: they also disturb the signal.

---

## 5. Connect the RX to the API

1. Start the API (and the frontend), sign in as the facility manager, open **Devices**, register the RX board's MAC
   (`7c:4f:ad:26:05:78` for the board used so far) in the right room with data source **LIVE HARDWARE**, and copy the
   device token that is shown once.
2. Run the bridge (close any `idf.py monitor` first):

```powershell
pip install pyserial
python tools\csi_serial_bridge.py --port COM4 --token TK-ESP32-... --api http://127.0.0.1:8000
```

After about 2 s the RX OLED switches to `bridge connected`, with the presence line (for example `NO PRESENCE`) and
`NOT TRAINED` until a model exists.

---

## 6. Make the predictions right: calibrate and train in THIS room

### Why the earlier prediction was wrong

The fall/activity model in `app/ml` was trained on the public **WiFall** dataset: other rooms, other hardware, other people.
Wi-Fi CSI depends heavily on the room and the board placement, so that model **does not transfer** to your room. Its live
output was close to guessing, which is why live fall detection is switched off (`LIVE_FALL_DETECTION=0`). No generic model
will be accurate in a new room. The fix is to train on recordings **from this room, with these boards, in this position**.

The in-room learner was improved for this:

* **New situations:** *Someone sitting or lying still* and *Someone walking*, in addition to *Empty*, *A few people* and *Busy*.
  Only the situations you record are ever predicted.
* **New features:** the old features only measured how much the signal fluctuates, so a person sitting still looked exactly
  like an empty room. The learner now also uses the mean RSSI and the **shape of the signal across the subcarriers**. A body
  in the radio path absorbs and reflects part of the band, which changes that shape even when the person does not move.
* Recordings made before this update are ignored automatically (they lack the new features). Record them again.

### Steps (Sensing Monitor → LIVE HARDWARE → *Learn this room*)

1. **Empty-room baseline (movement indicator):** everyone out, nothing moving, wait 15 s, press *Record empty-room baseline*.
2. Record **30 s of each situation**, each one **twice**, ideally at different times of day:
   * **Empty room**: everyone outside the area between the boards.
   * **Someone still**: one person sits on the chair or lies on the bed between the boards and stays still, breathing normally.
   * **Someone walking**: one person walks back and forth between the boards at a normal pace.
3. Press **Train the model** and read the result honestly:
   * **Held-out accuracy**: measured on the last 30 % of every recording, which the model never saw during training.
   * **Confusion matrix**: shows which situations get mixed up (usually *still* vs *empty*).
   * The model is marked **reliable** only when held-out accuracy is ≥ 75 % *and* clearly better than always guessing the most common situation.
4. If it is **not reliable**: record each situation again (longer, or with the still person in the exact spot they will
   usually be), then train again.
5. **Check it on another day.** Accuracy measured on one session is optimistic. Furniture, doors and temperature change the
   signal. If the live answers drift, record again.

The RX OLED then shows the learned state, for example **WALKING 87%**. A `?` after the number means the model was **not**
marked reliable.

### What "perfect" can and cannot mean here

No Wi-Fi sensing system is perfect, and claiming so in a report or viva would be challenged. What you *can* honestly show:
a model trained in the room, a held-out accuracy and a confusion matrix, and a re-check on a different day. One TX/RX pair
cannot count people, locate them or tell who they are. A person standing perfectly still can look like an empty room unless
the *still* situation was recorded at that spot. **Falls stay off for live hardware:** a fall model needs many labelled falls
recorded safely (on a crash mat) in this room, and an unvalidated "fall" alert is worse than none.

---

## 7. Troubleshooting

| Symptom | Likely cause → fix |
|---|---|
| OLED blank, log says `no SSD1306` | VCC/GND swapped or on 5V, SDA/SCL swapped, or the wire is not on GPIO 8/9. Re-check section 1. |
| OLED shows random dots / garbage | Loose jumper or a long wire. Keep the I²C wires under 20 cm and press them firmly into the breadboard. |
| TX turns off after a minute on the power bank | Power-bank auto-off. Use a wall charger (section 0). |
| RX `CSI 0/s`, `no frames from TX` | TX unpowered, antenna missing, boards too far apart, or different firmware/channel. |
| RX `dropped` keeps rising | Frames in the wrong format: re-flash `csi_send` (6 Mbps legacy OFDM, channel 11). |
| RX says `start the bridge` but the bridge runs | The bridge is on the native "USB" port: move the cable to the **COM/UART** port, or ignore it (data still flows; only the OLED state line needs the UART port). |
| `PC LINK LOST` | The bridge stopped or the API is unreachable: check the bridge window. |
| Predictions flip constantly | Boards moved, or not enough recordings: record each situation again (section 6). |
| Bridge stops with `rejected the device token` | Wrong or rotated token: copy a fresh one from the Devices page. |
