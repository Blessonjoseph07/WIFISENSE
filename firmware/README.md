# ESP32-S3 CSI firmware (transmitter + receiver)

Two small ESP-IDF projects (built and tested for compilation with ESP-IDF v6.1, target `esp32s3`):

| Project | Role | What it does |
|---|---|---|
| `csi_send` | TX board | Sends ~100 ESP-NOW broadcast frames/s from fixed MAC `1a:00:00:00:00:00`, channel 11, HT20, **legacy OFDM 6 Mbps**. Never talks to the API. |
| `csi_recv` | RX board (the registered LIVE device) | Captures CSI (20 MHz, legacy LTF only), converts the 52 used subcarriers to the API's 104 I/Q values and prints one line per packet on USB serial. Keeps its own hardware MAC. |

```
TX board --Wi-Fi frames--> RX board --USB serial--> tools/csi_serial_bridge.py --HTTP--> API (/sensing/ingest) --> dashboard
```
The bridge runs on the PC next to the RX board, so no Wi-Fi password, router channel, firewall rule or device token is
stored on the chip. (Posting straight from the chip over Wi-Fi is possible later; it needs the RX to join the router, which
forces both boards onto the router's channel.)

## Why these radio settings
The detector was trained on 52 subcarriers (20 MHz, legacy long training field). The earlier example setup (HT40, HT-LTF,
STBC, LTF merge, MCS0) produces a different buffer, which the API cannot use. `csi_recv` drops, and counts, any frame whose
`sig_mode`/`cwb` is not non-HT 20 MHz or whose CSI length is not **128**, instead of converting it.

## Build (already verified to compile on v6.1)
In an ESP-IDF PowerShell:
```powershell
cd firmware\csi_recv ; idf.py set-target esp32s3 ; idf.py build
cd ..\csi_send       ; idf.py set-target esp32s3 ; idf.py build
```

## Flash (use each board's own COM port; close any serial monitor first)
```powershell
cd firmware\csi_recv ; idf.py -p COM4 flash     # RX board, MAC 7c:4f:ad:26:05:78
cd ..\csi_send       ; idf.py -p COMx flash     # TX board
```
Both boards must run on the same channel (11) within range of each other. Keep the TX board powered from a USB charger or
the PC; it does not need a serial connection.

## Check the receiver before bridging
```powershell
cd firmware\csi_recv ; idf.py -p COM4 monitor
```
You should see `RX ready: channel 11 HT20, lltf-only CSI (expect len=128) ...` and then lines starting `CSI_IQ,`. If you see
`dropped CSI: len=...` or `dropped frame: sig_mode=...`, the TX board is not sending 6 Mbps legacy OFDM on channel 11.
The `CSI_IQ` lines (208 hex digits = 104 int8 values) are sent through the normal console, which is mirrored to both the
UART port and the native USB port (Windows lists the native one as "USB Serial Device"), so either cable works.

## Bridge to the API
```bash
pip install pyserial        # once, in the Python you run the bridge with
python tools/csi_serial_bridge.py --port COM4 --token TK-ESP32-... --api http://127.0.0.1:8000
```
Close `idf.py monitor` first (only one program can open the port). Add `--dry-run` to parse and verify without sending.
Every ~256th packet the receiver also prints `CSI_RAW` (the 128-value buffer); the bridge converts it with the Python
reference and **stops** if the firmware's own conversion disagrees. Watch the result with
`python tools/hardware_link_check.py watch --mac 7c:4f:ad:26:05:78` and in Sensing Monitor > LIVE HARDWARE > CSI packet stream.

## Not verified here
Nothing in this folder has run on a board yet: it compiles, the bridge and the conversion are tested against a reference and a
synthetic capture, but whether the TX frames really arrive with CSI length 128 on your two boards is the first thing to check
with `monitor`.
