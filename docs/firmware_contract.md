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
    // Compact alternative accepted by the API: "iq_b64": base64 of the same 104 signed bytes (use this OR "iq", not both).
    // The bridge uses it by default (about 43% smaller requests); the stored format is the same.
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

## 3b. Required radio configuration (the detector only understands this layout)
The model behind the detector was trained on 52 subcarriers, so the firmware must produce that and nothing else:
- **20 MHz only, legacy long training field only.** `esp_wifi_set_bandwidth(WIFI_IF_STA, WIFI_BW_HT20)` on RX and TX, and
  ```c
  wifi_csi_config_t cfg = { .lltf_en = true, .htltf_en = false, .stbc_htltf2_en = false,
                            .ltf_merge_en = false, .channel_filter_en = false, .manu_scale = false, .shift = 0 };
  ```
  `htltf_en`, `stbc_htltf2_en`, `ltf_merge_en` or an HT40 channel change the buffer length and slot order. The API does not
  support those layouts (the buffer is then not 128 bytes). A 114-subcarrier or 40 MHz stream would need a new model.
- **The TX frames must be OFDM, not 1 Mbps DSSS.** ESP-NOW defaults to 1 Mbps and DSSS frames produce no CSI. Set a legacy
  OFDM rate (for example 6 Mbps) on the sender. The exact call depends on the IDF version (`esp_now_set_peer_rate_config`
  in IDF 5.x, `esp_wifi_config_espnow_rate` earlier).
- **Same channel.** The RX must be connected to the router to POST over HTTP, so the TX must transmit on the router's channel
  (`esp_wifi_set_channel`). The RX bandwidth setting does not need to match the router.
- **First check:** log `info->len` in the CSI callback. With the settings above it is **128**. Anything else means the
  configuration is not the one this contract describes.
- Cross-check the C extraction against `tools/csi_buffer_to_iq.py` (`--selftest`, then `--buf` with a real 128-value dump):
  the 104 values must match exactly. The tool also reports non-zero energy in the guard/DC slots, which means the slot
  order is wrong.

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
