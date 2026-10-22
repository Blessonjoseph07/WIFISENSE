# ESP32-S3 firmware contract (receiver module -> API)

The system is one TX module and one RX module. The **RX module** posts its CSI to the API; the TX module only transmits
frames (ESP-NOW or Wi-Fi) at a steady rate, 50-100 per second. The RX is the "device" the application knows.

## 1. Register the RX as a LIVE device
As `system_admin` or `facility_manager`: `POST /devices` with `allowed_source: "live"` and the RX MAC. The response
contains `hardware_token` **once**. Flash it into the RX firmware. A LIVE device can only send LIVE packets; the API
rejects anything labelled simulated or dataset.

## 2. Send packets
`POST https://<api>/sensing/ingest`, headers `Content-Type: application/json` and `X-Device-Token: <hardware_token>`.
Batch 5-20 packets per request (max 100). Body:

```json
{"packets": [{
  "sequence_number": 1234,          // RX counter, increments per CSI callback (wraps at 65535 is fine)
  "rssi": -52,                      // dBm, from rx_ctrl.rssi            (required, -120..0)
  "noise_floor": -92,               // dBm, from rx_ctrl.noise_floor
  "channel": 6,                     // primary channel
  "bandwidth_mhz": 20,
  "subcarrier_count": 52,
  "csi_data": {
    "iq": [I0, Q0, I1, Q1, ... ],   // EXACTLY 104 integers: 52 subcarriers, I first then Q  (required for detection)
    "src_mac": "24:0A:C4:..",       // the TX MAC (rx_ctrl.mac)
    "rate": 11, "sig_mode": 0, "mcs": 0, "cwb": 0, "agc_gain": 30, "fft_gain": 12   // optional extras, shown in the UI
  }
}]}
```
Omit `timestamp` unless the device has real time (NTP); the server stamps arrival time.
Never put `label`, `activity`, `class`, `event_type` or similar keys in `csi_data`: the API rejects them.

## 3. IQ ordering (important)
ESP-IDF's `wifi_csi_info_t.buf` holds int8 pairs **imaginary first, then real**. The API expects `[I, Q]` = `[real, imag]`,
so swap each pair. With only the legacy long training field enabled (20 MHz, non-HT) the buffer has 64 subcarrier slots
ordered 0..31 then -32..-1. Send the 52 used subcarriers in the order -26..-1, 1..26:

```c
// buf: int8_t[128] from the CSI callback, out: int8_t[104]
int n = 0;
for (int k = -26; k <= 26; k++) {
    if (k == 0) continue;
    int slot = (k >= 0) ? k : 64 + k;      // 0..31, then -32..-1 stored at 32..63
    out[n++] = buf[2 * slot + 1];          // real  -> I
    out[n++] = buf[2 * slot];              // imag  -> Q
}
```
Check this against the IDF version you build with (slot order differs if HT-LTF or 40 MHz is enabled). A wrong order
still uploads but shows garbled phase and waterfall structure in the CSI packet stream panel.

## 4. What the dashboard derives from this
Sensing Monitor > pick the LIVE device > **CSI packet stream**: packet rate, loss (sequence gaps), RSSI/noise/SNR, amplitude
and sanitised phase per subcarrier, an amplitude waterfall, dominant fluctuation frequency, and the radio link
(frequency and wavelength derived from `channel`; spacing 312.5 kHz). The detector needs windows of >= 100 packets.

## 5. What it cannot show
A single TX-RX pair does not give x/y coordinates of a person. The panel shows channel measurements and a motion
indicator, never a position. Coordinates would need several RX nodes and a calibration step.

## 6. Test without hardware
`python tools/esp32_emulator.py --token <DEMO device token> --activity walking` posts the same format to a device
registered with `allowed_source: "simulated"`. Everything it sends is badged DEMO.
