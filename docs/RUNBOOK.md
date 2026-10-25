# Wi-Fi Sense runbook: running everything, step by step

This is the practical guide to running the project: the two ESP32-S3 boards, the bridge, the website, real recorded
CSI (dataset replay), the hosted site, and every role's functions. For wiring and flashing the boards, see
[hardware_build_guide.md](hardware_build_guide.md).

```
 TX board (power bank)  --Wi-Fi frames-->  RX board  --USB-->  bridge (on the laptop)  --HTTP-->  API  -->  website
  OLED: SENDING + waves                     OLED: CSI rate,      tools/csi_serial_bridge.py        |        (Sensing Monitor)
                                            presence, room state  <---- presence / room state ------+
```

**The three data modes, never mixed:**

| Mode | Where the data comes from | Shown as |
|---|---|---|
| **LIVE HARDWARE** | your RX board, through the bridge, right now | LIVE HARDWARE |
| **DATASET REPLAY** | real CSI recorded by other researchers (WiFall), replayed through the same pipeline | DATASET REPLAY |
| **DEMO** | generated preview values (seeded rooms, the emulator) | orange dot / DEMO |

---

## 1. Accounts

Local development passwords are `<name>password`. On the hosted site the administrator may have set different ones.

| Role | Email | Password (local) | Main pages |
|---|---|---|---|
| System admin | `blesson@wifisense.com` | `blessonpassword` | System Admin Console, **Sensing Monitor**, **Devices & Service Desk**, Evidence & Limits, Staff & Organization |
| Care facility manager | `elizabeth@wifisense.com` | `elizabethpassword` | Monitoring Dashboard, Staff & Organization (helpline), Sharing Policies, Family Portal approvals, Sensing Monitor |
| Corporate facility manager | `abhinand@wifisense.com` | `abhinandpassword` | Corporate Workplace, Room Scheduling, Analytics & Telemetry, Devices |
| Caregiver | `mary@wifisense.com` | `marypassword` | Monitoring Dashboard, Elder Care & Safety, Alerts & Incidents |
| Corporate staff | `tomy@wifisense.com` | `tomypassword` | Corporate Workplace, Room Scheduling |
| Doctor | `mathew.varghese@wifisense.com` | `doctorpassword` | Medical Portal |
| Family member | `john@wifisense.com` | `johnpassword` | Family Portal |
| Payment test family member | `payer@wifisense.com` | `payerpassword` | Family Portal, with no plan yet (for the payment flow) |

Your receiver (`7c:4f:ad:26:05:78`) is in the room **Research Lab 2 - Embedded CSI**, which belongs to the corporate
organization. For training and live hardware, use the **system admin**: the Sensing Monitor page is in the admin's menu.

---

## 2. Every day: start a live hardware session (local)

1. **TX board**: connect it to the power bank. Its screen shows **SENDING** with the waves.
2. **RX board**: plug it into the laptop (either USB-C port works; it is usually **COM4**). Its screen lights up.
3. **One-time setup, the device token** (skip if you already did it):
   1. Double-click **`start-live.bat`**. Without a token it starts only the API and the website.
   2. Open <http://localhost:5173>, sign in as **blesson**, go to **Devices & Service Desk**.
   3. On the row **7c:4f:ad:26:05:78**, press **RESET TOKEN** and copy the token from the box (it is shown once).
   4. In a terminal: `setx WIFISENSE_DEVICE_TOKEN "TK-ESP32-..."`, then close the start-live windows.
4. **Start everything**: double-click **`start-live.bat`** (or run `start-live.bat COM3` for another port). It opens
   three windows: **API** (hardware database), **Website**, and **Bridge**.
5. **Check that it works**:
   * Bridge window: `read=... (90/s) sent=... http_errors=0 last_http=201`, counting up.
   * RX screen: `CSI ~90/s RSSI -4x`, then `bridge connected`, with `NO PRESENCE` or `PRESENCE+MOVE`.
   * Website: **Sensing Monitor → LIVE HARDWARE**: the device is **ONLINE** and "board is sending data".

**Manual start** (what start-live.bat does), in three PowerShell windows from `D:\Wifisense`:
```powershell
cd backend; $env:DATABASE_URL="sqlite:///./hardware_test.db"; venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
cd frontend; npm run dev
backend\venv\Scripts\python tools\csi_serial_bridge.py --port COM4 --token TK-ESP32-... --api http://127.0.0.1:8000
```

`start-all.bat` starts the API on the main database (`wifisense.db`), where your live receiver is not registered. For
live hardware always use `start-live.bat`.

**Only one program can open the COM port.** Close `idf.py monitor` and any other bridge before starting one.

---

## 3. What the boards' screens mean

**Transmitter**

| Screen | Meaning |
|---|---|
| **SENDING** + waves moving out | transmitting about 100 frames per second on channel 11 |
| **SEND ERR**, no waves | sending is failing: power cycle it |
| goes dark after a minute | the power bank cut out at low load: use a phone charger |

**Receiver**

| Line | Meaning |
|---|---|
| `CSI 90/s RSSI -45` | frames received from the TX per second, and their signal strength (measured on the board) |
| `dropped N` | frames in the wrong format (should stay 0) |
| `NO PRESENCE` / `PRESENCE` / `PRESENCE+MOVE` | the movement check: the signal compared with this room's empty level |
| `EMPTY 74%` / `STILL 68%` / `WALKING 91%` | the model trained in this room (section 4). **`?`** = the model is not marked reliable |
| `PRESENCE 90%` | clear movement: the share of the last 10 seconds above the empty-room level (a count, not a guess) |
| `NOT TRAINED` | no room model yet |
| `bridge connected` / `start the bridge` / `PC LINK LOST` | whether the bridge is sending the display line |
| `no frames from TX` | the TX is off, out of range, or on another channel |

The movement check always decides **moving vs not moving**. The model only chooses within that: it can never show
WALKING without movement, or STILL during clear movement.

---

## 4. Teach the room (machine learning)

Do this once per board placement. If either board moves, do it again.

**Placement:** boards 2–3 m apart, about 1 m high, antennas vertical. Put a chair **exactly on the straight line between
the two antennas**: for "still", your body must be **in** the radio path. Sitting beside the line looks exactly like an
empty room to the radio.

On **Sensing Monitor → LIVE HARDWARE** (signed in as blesson):

1. **Record empty-room baseline**: nobody between the boards, nothing moving, wait 15 s, press the button.
2. **Learn this room → Record 30 s**, each situation **twice**:
   * **Empty room**: nobody in the area.
   * **Someone sitting or lying still**: sit on the chair on the line, still, breathing normally.
   * **Someone walking**: walk back and forth between the boards at a normal pace.
3. **Train the model**, then read the result:
   * **Accuracy**: with 2+ recordings per situation, each recording is tested by a model that was trained **without
     it** (leave-one-recording-out). This is the honest number. With one recording per situation, the model is never
     called reliable.
   * **Table**: rows are the truth, columns the model's answer. Look at which situations get mixed up.
   * **Reliable**: accuracy ≥ 75 % *and* clearly better than always guessing the commonest situation.
   * **Confidence %** on the screen is scaled down by the measured error, so a model that is right 80 % of the time
     cannot show 99 %.
4. **If "still" mixes with "empty"**: your body was not in the radio path. Move the chair onto the line, use **Clear
   everything**, and record all six again in one session.

What one TX/RX pair can and cannot do: it detects **movement** very reliably and can learn **still vs empty** when the
body blocks the direct path. It cannot count, locate or identify people. **Fall detection is off for live hardware**:
a fall model needs many labelled falls recorded safely (on a crash mat) in this room.

---

## 5. Real recorded CSI: DATASET REPLAY

This shows the detector working on **real CSI recorded by researchers** (WiFall: 928 clips, 10 people, ESP32-S3,
actions fall/jump/sit/stand/walk), replayed through the same authenticated pipeline. It is labelled **DATASET
REPLAY** everywhere, never LIVE, and it never pages anyone.

1. **Download** `WiFall.zip` (29 MB) from <https://huggingface.co/datasets/RS2002/WiFall> and extract it, for example
   to `D:\data\WiFall`, so that `D:\data\WiFall\ID0 … ID9` exist. Do not commit it (licence not stated).
2. **The replay device** already exists: `02:57:49:46:41:4c` in **Resident Room 101** (data source DATASET REPLAY).
   In **Devices & Service Desk** press **RESET TOKEN** on it and copy the token.
3. **Run the replay** (API running, any terminal, from `D:\Wifisense`):
   ```powershell
   $env:WIFISENSE_API_BASE="http://127.0.0.1:8000"
   $env:WIFISENSE_DEVICE_TOKEN="TK-..."            # the replay device's token, not the receiver's
   $env:WIFISENSE_ADMIN_EMAIL="blesson@wifisense.com"
   $env:WIFISENSE_ADMIN_PASSWORD="blessonpassword"
   backend\venv\Scripts\python tools\replay_wifall.py --data-dir D:\data\WiFall --limit 32
   ```
   By default only the person the model **never saw in training** is replayed, so the result is an honest test.
   `--limit 32` keeps it short; leave it out for the full set; `--skip N` resumes an interrupted run.
4. **Show it**:
   * **Sensing Monitor → DATASET REPLAY**: the replayed packets, the detector's decisions and the plain-language summary.
   * **Evidence & Limits**: the detector's results compared with the recorded labels (accuracy on the unseen person,
     the baselines) and what the model can and cannot claim.

---

## 6. Demo data and the emulator

The seeded rooms (Resident Room 101–2xx, conference rooms) show **DEMO** values, marked with an orange dot, so every
screen can be shown without hardware. To feed a DEMO device with emulated CSI:
```powershell
backend\venv\Scripts\python tools\esp32_emulator.py --api http://127.0.0.1:8000 --token TK-... --activity walking
```
It refuses to target LIVE devices, and everything it sends is badged DEMO.

---

## 7. The hosted site

* **Website** <https://wifisense-ecru.vercel.app>, **API** <https://wifisense-api.onrender.com> (`/docs` for Swagger).
* It has its **own database** (Supabase), separate from your laptop: devices, tokens and training are per database.
* **Before presenting**, wake it and check it (10–15 minutes before):
  ```powershell
  backend\venv\Scripts\python tools\presentation_preflight.py --api https://wifisense-api.onrender.com --web https://wifisense-ecru.vercel.app
  ```
  The **Keep API warm** GitHub workflow also pings it every 10 minutes during the Indian day.
* **Live boards on the hosted site**: register `7c:4f:ad:26:05:78` there (Devices & Service Desk, data source LIVE
  HARDWARE), press **RESET TOKEN**, then run the bridge with `--api https://wifisense-api.onrender.com --token <hosted token>`.
  The bridge sends to one API at a time, and the room must be trained again on the hosted site.

---

## 8. Every function, role by role

**Caregiver (mary)**: Monitoring Dashboard
1. **Room feed**: each room's status (occupied, activity, fall risk), with DEMO / LIVE marking.
2. **Emergency fall alert**: a new possible fall takes over the screen (only falls from the last 30 minutes; older
   open ones stay in the banner). **Confirm detection** or **Dismiss as false alarm** (a note is required), then
   **Acknowledge → Responding → Resolve**.
3. **Alerts & Incidents**: the list and history; **Elder Care & Safety**: residents, care records.

**Care facility manager (elizabeth)**
1. **Staff & Organization**: staff accounts, and the **Care home helpline**. The number is checked as you type: Indian
   numbers need 10 digits after +91; 10-digit mobile/landline, 0 + 10 digits, or 1800 toll-free without +91. Families
   see it in their portal.
2. **Sharing Policies**: what families may see (presence, activity detail, room, safety notifications, severity).
3. **Family Portal (approvals)**: approve or reject family members' link requests.
4. **Medical Providers**: approve doctors and assign their residents.
5. **Devices & Service Desk**: register nodes, **RESET TOKEN**, report faults.
6. **Sensing Monitor / Evidence & Limits**: as in sections 4 and 5.

**Family member (john / payer)**: Family Portal
1. **Presence**: a dignified "Presence detected" for their relative, filtered by the sharing policy.
2. **Safety incidents** and the care home's **helpline**.
3. **Care Plan (Razorpay test mode, no real money)**: sign in as **payer**, choose the plan, pay with test card
   `4111 1111 1111 1111` (any future expiry, any CVV) or UPI `success@razorpay`.

**Doctor (mathew.varghese)**: Medical Portal: assigned residents, consultation notes, mobility history.

**Corporate (abhinand, tomy)**: Corporate Workplace (room occupancy and utilisation, energy: switch off HVAC/lighting
in vacant rooms), Room Scheduling, Analytics & Telemetry.

**System admin (blesson)**: everything above across all organizations, plus the System Admin Console (tenants, audit
logs, device diagnostics).

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| Bridge: `could not open port` / `Access is denied` | another program has the COM port: close `idf.py monitor` or the other bridge |
| Bridge: `ClearCommError` and it stops | the receiver's USB disconnected: plug it back in and start the bridge again |
| Bridge: `rejected the device token (401)` | wrong or replaced token: RESET TOKEN on the device, update `WIFISENSE_DEVICE_TOKEN` |
| Bridge: `HTTP errors`, `retries` going up | the API is not running or restarting: check the API window |
| RX screen `start the bridge` | the bridge is not running, or the RX runs old firmware: re-flash `csi_recv` |
| RX screen `CSI 0/s`, `no frames from TX` | TX unpowered, antenna missing, or out of range |
| Website: device OFFLINE | nothing has arrived for 20 s: check the bridge window |
| Website: "Failed to fetch" at login | the API is not running, or you opened a different address than localhost:5173 |
| Model says the wrong thing | record again (section 4): placement changed, or "still" was not in the radio path |
| Hosted site slow at first | free hosting wakes up in about 50 s: run the preflight before presenting |
| OLED dark | read the boot log (`idf.py -p COM4 monitor`): see hardware_build_guide.md, Troubleshooting |

---

## 10. Before the viva: checklist

- [ ] TX on a charged power bank, RX plugged in, both screens showing data.
- [ ] `start-live.bat`: bridge `http_errors=0`, website device ONLINE.
- [ ] Room trained (2 recordings per situation), result marked **reliable**; note the accuracy and the table.
- [ ] WiFall replay done once; **Evidence & Limits** shows the unseen-person result.
- [ ] Hosted site: preflight passed.
- [ ] Be ready to explain honestly: what one TX/RX pair can detect (movement; still vs empty only in the radio path),
      why live fall detection is off, and how accuracy is measured on recordings the model never saw.
