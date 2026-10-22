/*
 * Wi-Fi Sense CSI receiver (ESP32-S3).
 *
 * Captures CSI from the transmitter's frames and prints one line per packet on the USB serial port. A PC-side bridge
 * (tools/csi_serial_bridge.py) turns the lines into batches for POST /sensing/ingest with the device token, so no Wi-Fi
 * credentials, router channel or token are stored on the chip.
 *
 * Radio configuration required by the API's detector (see docs/firmware_contract.md):
 *   - 20 MHz channel, legacy long training field only (lltf_en = true, everything else off) => the CSI buffer is exactly
 *     128 bytes = 64 subcarrier slots of (imag, real), slot order 0..31 then -32..-1.
 *   - The 52 used subcarriers (-26..-1, 1..26) are converted here to 104 values in the API's (real, imag) order.
 * Frames that are not that layout are counted and dropped, never converted.
 *
 * The receiver keeps its own hardware MAC (that is the identity registered in the API). The transmitter's fixed source MAC
 * is only used as a filter.
 * Derived from Espressif's esp-csi csi_recv example (Apache-2.0 / CC0).
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "nvs_flash.h"
#include "esp_mac.h"
#include "rom/ets_sys.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_now.h"
#include "esp_idf_version.h"

/* IDF 6 renamed WIFI_BW_HT20 to WIFI_BW20. */
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(6, 0, 0)
#define WS_BW_20MHZ WIFI_BW20
#else
#define WS_BW_20MHZ WIFI_BW_HT20
#endif

#define WIFISENSE_CHANNEL   11            /* must be the same on the transmitter */
#define CSI_BUF_LEN         128           /* 64 slots x (imag, real), 20 MHz legacy LTF */
#define SLOTS               64
#define N_SUBCARRIERS       52
#define RAW_DUMP_EVERY      256           /* every Nth packet also prints the raw buffer, to verify the conversion */

static const uint8_t TX_MAC[6] = {0x1a, 0x00, 0x00, 0x00, 0x00, 0x00};
static const char *TAG = "wifisense_rx";

static void wifi_init(void)
{
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    ESP_ERROR_CHECK(esp_netif_init());
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_bandwidth(WIFI_IF_STA, WS_BW_20MHZ));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_ERROR_CHECK(esp_wifi_set_channel(WIFISENSE_CHANNEL, WIFI_SECOND_CHAN_NONE));
}

static void esp_now_setup(void)
{
    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_set_pmk((const uint8_t *)"pmk1234567890123"));
    esp_now_peer_info_t peer = {
        .channel   = WIFISENSE_CHANNEL,
        .ifidx     = WIFI_IF_STA,
        .encrypt   = false,
        .peer_addr = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
    };
    ESP_ERROR_CHECK(esp_now_add_peer(&peer));
}

static void csi_rx_cb(void *ctx, wifi_csi_info_t *info)
{
    static uint32_t accepted = 0, dropped_len = 0, dropped_fmt = 0, fallback_seq = 0;

    if (!info || !info->buf || memcmp(info->mac, TX_MAC, 6) != 0) {
        return;
    }
    const wifi_pkt_rx_ctrl_t *rc = &info->rx_ctrl;

    /* Only 20 MHz non-HT frames with the layout the API understands. */
    if (rc->sig_mode != 0 || rc->cwb != 0) {
        if ((dropped_fmt++ % 500) == 0) {
            ESP_LOGW(TAG, "dropped frame: sig_mode=%d cwb=%d (need non-HT 20 MHz; check the transmitter's rate/bandwidth) [%u so far]",
                     (int)rc->sig_mode, (int)rc->cwb, (unsigned)dropped_fmt);
        }
        return;
    }
    if (info->len != CSI_BUF_LEN) {
        if ((dropped_len++ % 500) == 0) {
            ESP_LOGW(TAG, "dropped CSI: len=%d, expected %d (check lltf-only CSI config) [%u so far]",
                     (int)info->len, CSI_BUF_LEN, (unsigned)dropped_len);
        }
        return;
    }

    /* Sequence number the transmitter put in the ESP-NOW payload (same offset as the esp-csi examples). */
    uint32_t seq = fallback_seq++;
    if (info->payload != NULL && info->payload_len >= 19) {
        memcpy(&seq, info->payload + 15, sizeof(seq));
    }

    /* ESP-IDF stores (imag, real) per slot, slots 0..31 then -32..-1. The API wants (real, imag) for -26..-1, 1..26. */
    int8_t iq[2 * N_SUBCARRIERS];
    int n = 0;
    for (int k = -26; k <= 26; k++) {
        if (k == 0) {
            continue;
        }
        int slot = (k >= 0) ? k : SLOTS + k;
        iq[n++] = info->buf[2 * slot + 1];   /* real -> I */
        iq[n++] = info->buf[2 * slot];       /* imag -> Q */
    }

    if (accepted == 0) {
        ets_printf("type,seq,mac,rssi,rate,sig_mode,mcs,cwb,noise_floor,channel,first_word_invalid,iq\n");
    }
    ets_printf("CSI_IQ,%u," MACSTR ",%d,%d,%d,%d,%d,%d,%d,%d,[%d",
               (unsigned)seq, MAC2STR(info->mac), rc->rssi, rc->rate, rc->sig_mode, rc->mcs, rc->cwb,
               rc->noise_floor, rc->channel, (int)info->first_word_invalid, iq[0]);
    for (int i = 1; i < 2 * N_SUBCARRIERS; i++) {
        ets_printf(",%d", iq[i]);
    }
    ets_printf("]\n");

    if ((accepted % RAW_DUMP_EVERY) == 0) {
        ets_printf("CSI_RAW,%u,[%d", (unsigned)seq, info->buf[0]);
        for (int i = 1; i < CSI_BUF_LEN; i++) {
            ets_printf(",%d", info->buf[i]);
        }
        ets_printf("]\n");
    }
    accepted++;
}

static void csi_init(void)
{
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
    wifi_csi_config_t csi_config = {
        .lltf_en           = true,    /* legacy long training field only: 52 subcarriers at 20 MHz */
        .htltf_en          = false,
        .stbc_htltf2_en    = false,
        .ltf_merge_en      = false,
        .channel_filter_en = false,   /* raw per-subcarrier values, no smoothing */
        .manu_scale        = false,
        .shift             = 0,
    };
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(csi_rx_cb, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));
}

void app_main(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    wifi_init();
    esp_now_setup();
    csi_init();

    uint8_t mac[6];
    ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_STA));
    ESP_LOGI(TAG, "RX ready: channel %d HT20, lltf-only CSI (expect len=%d), own MAC " MACSTR ", filtering source " MACSTR,
             WIFISENSE_CHANNEL, CSI_BUF_LEN, MAC2STR(mac), MAC2STR(TX_MAC));
}
