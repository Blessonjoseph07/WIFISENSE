/*
 * Wi-Fi Sense CSI receiver (ESP32-S3).
 *
 * Captures CSI from the transmitter's frames and prints one line per packet on the serial console. A PC-side bridge
 * (tools/csi_serial_bridge.py) turns the lines into batches for POST /sensing/ingest with the device token, so no Wi-Fi
 * credentials, router channel or token are stored on the chip.
 *
 * Output goes through the normal console, which ESP-IDF mirrors to BOTH the UART port and the native USB port (the one
 * Windows lists as "USB Serial Device"). Lines are formatted in the CSI callback (cheap, no printf) and printed by a
 * separate task, so a slow serial port drops lines (counted) instead of stalling the Wi-Fi task.
 *
 * Radio configuration required by the API's detector (see docs/firmware_contract.md):
 *   - 20 MHz channel, legacy long training field only (lltf_en = true, everything else off) => the CSI buffer is exactly
 *     128 bytes = 64 subcarrier slots of (imag, real), slot order 0..31 then -32..-1.
 *   - The 52 used subcarriers (-26..-1, 1..26) are converted here to 104 int8 values in the API's (real, imag) order.
 * Frames that are not that layout are counted and dropped, never converted.
 *
 * Line format (hex = two lowercase hex digits per int8, two's complement):
 *   CSI_IQ,seq,mac,rssi,rate,sig_mode,mcs,cwb,noise_floor,channel,first_word_invalid,<208 hex digits = 104 int8 I/Q>
 *   CSI_RAW,seq,<256 hex digits = the raw 128-byte buffer>     (every RAW_DUMP_EVERY-th packet, to verify the conversion)
 *
 * The receiver keeps its own hardware MAC (that is the identity registered in the API). The transmitter's fixed source MAC
 * is only used as a filter.
 * Derived from Espressif's esp-csi csi_recv example (Apache-2.0 / CC0).
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/stream_buffer.h"
#include "nvs_flash.h"
#include "esp_mac.h"
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
#define RAW_DUMP_EVERY      256
#define LINE_CAP            640
#define OUT_BUFFER_BYTES    (24 * 1024)

static const uint8_t TX_MAC[6] = {0x1a, 0x00, 0x00, 0x00, 0x00, 0x00};
static const char *TAG = "wifisense_rx";
static const char HEXD[] = "0123456789abcdef";

static StreamBufferHandle_t s_out;
static volatile uint32_t s_out_drops;

/* ---- tiny formatters (no printf in the Wi-Fi task) ---- */
static char *put_str(char *p, const char *s)
{
    while (*s) {
        *p++ = *s++;
    }
    return p;
}

static char *put_int(char *p, int v)
{
    char tmp[12];
    int n = 0;
    unsigned u;
    if (v < 0) {
        *p++ = '-';
        u = (unsigned)(-(long)v);
    } else {
        u = (unsigned)v;
    }
    do {
        tmp[n++] = (char)('0' + (u % 10));
        u /= 10;
    } while (u);
    while (n) {
        *p++ = tmp[--n];
    }
    return p;
}

static char *put_hex8(char *p, uint8_t b)
{
    *p++ = HEXD[b >> 4];
    *p++ = HEXD[b & 0x0f];
    return p;
}

static char *put_mac(char *p, const uint8_t *m)
{
    for (int i = 0; i < 6; i++) {
        p = put_hex8(p, m[i]);
        if (i < 5) {
            *p++ = ':';
        }
    }
    return p;
}

static void out_line(const char *s, size_t n)
{
    if (xStreamBufferSpacesAvailable(s_out) < n) {
        s_out_drops++;                      /* never send half a line */
        return;
    }
    xStreamBufferSend(s_out, s, n, 0);
}

static void print_task(void *arg)
{
    static char chunk[512];
    for (;;) {
        size_t n = xStreamBufferReceive(s_out, chunk, sizeof(chunk), portMAX_DELAY);
        if (n) {
            fwrite(chunk, 1, n, stdout);
            fflush(stdout);
        }
    }
}

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
    static char line[LINE_CAP];            /* the callback runs in one task, so a static buffer is safe */

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
    char *p = line;
    p = put_str(p, "CSI_IQ,");
    p = put_int(p, (int)(seq & 0x7fffffff));
    *p++ = ',';
    p = put_mac(p, info->mac);
    *p++ = ','; p = put_int(p, rc->rssi);
    *p++ = ','; p = put_int(p, rc->rate);
    *p++ = ','; p = put_int(p, rc->sig_mode);
    *p++ = ','; p = put_int(p, rc->mcs);
    *p++ = ','; p = put_int(p, rc->cwb);
    *p++ = ','; p = put_int(p, rc->noise_floor);
    *p++ = ','; p = put_int(p, rc->channel);
    *p++ = ','; p = put_int(p, (int)info->first_word_invalid);
    *p++ = ',';
    for (int k = -26; k <= 26; k++) {
        if (k == 0) {
            continue;
        }
        int slot = (k >= 0) ? k : SLOTS + k;
        p = put_hex8(p, (uint8_t)info->buf[2 * slot + 1]);   /* real -> I */
        p = put_hex8(p, (uint8_t)info->buf[2 * slot]);       /* imag -> Q */
    }
    *p++ = '\n';
    out_line(line, (size_t)(p - line));

    if ((accepted % RAW_DUMP_EVERY) == 0) {
        p = line;
        p = put_str(p, "CSI_RAW,");
        p = put_int(p, (int)(seq & 0x7fffffff));
        *p++ = ',';
        for (int i = 0; i < CSI_BUF_LEN; i++) {
            p = put_hex8(p, (uint8_t)info->buf[i]);
        }
        *p++ = '\n';
        out_line(line, (size_t)(p - line));
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

    s_out = xStreamBufferCreate(OUT_BUFFER_BYTES, 1);
    configASSERT(s_out != NULL);
    xTaskCreate(print_task, "csi_print", 4096, NULL, tskIDLE_PRIORITY + 2, NULL);

    wifi_init();
    esp_now_setup();
    csi_init();

    uint8_t mac[6];
    ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_STA));
    ESP_LOGI(TAG, "RX ready: channel %d HT20, lltf-only CSI (expect len=%d), own MAC " MACSTR ", filtering source " MACSTR,
             WIFISENSE_CHANNEL, CSI_BUF_LEN, MAC2STR(mac), MAC2STR(TX_MAC));

    for (;;) {                               /* report output drops (a serial port that cannot keep up) */
        vTaskDelay(pdMS_TO_TICKS(10000));
        if (s_out_drops) {
            ESP_LOGW(TAG, "serial output dropped %u lines so far (port too slow or not read)", (unsigned)s_out_drops);
        }
    }
}
