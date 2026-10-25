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
 *
 * Optional SSD1306 OLED (components/wifisense_oled): shows the CSI rate, RSSI and drops measured here, plus one line the
 * bridge writes back every ~2 s on either USB port (UART or native USB):  WS_STATE,<presence text>,<room state text>
 * (the API's answer for this device; the board itself never classifies anything).
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
#include "esp_timer.h"
#include "driver/uart.h"
#include "hal/usb_serial_jtag_ll.h"
#include "wifisense_oled.h"

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
static volatile uint32_t s_accepted, s_dropped;
static volatile int s_last_rssi;

/* Latest WS_STATE line from the bridge (written by state_rx_task, read by display_task). */
static portMUX_TYPE s_state_lock = portMUX_INITIALIZER_UNLOCKED;
static char s_presence[17] = "WAITING FOR PC";
static char s_room[17] = "";
static int64_t s_state_at_us;

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
        s_dropped++;
        if ((dropped_fmt++ % 500) == 0) {
            ESP_LOGW(TAG, "dropped frame: sig_mode=%d cwb=%d (need non-HT 20 MHz; check the transmitter's rate/bandwidth) [%u so far]",
                     (int)rc->sig_mode, (int)rc->cwb, (unsigned)dropped_fmt);
        }
        return;
    }
    if (info->len != CSI_BUF_LEN) {
        s_dropped++;
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
    s_accepted = accepted;
    s_last_rssi = rc->rssi;
}

/* One reader per port: collects bytes into a line and stores a complete WS_STATE line for the display. */
typedef struct {
    char line[64];
    size_t n;
} state_reader_t;

static void state_feed(state_reader_t *r, uint8_t c)
{
    if (c != '\n') {
        if (r->n < sizeof(r->line) - 1) {
            r->line[r->n++] = (char)c;
        }
        return;
    }
    char *line = r->line;
    line[r->n] = 0;
    r->n = 0;
    if (strncmp(line, "WS_STATE,", 9) != 0) {
        return;
    }
    char *top = line + 9, *bottom = strchr(top, ',');
    if (!bottom) {
        return;
    }
    *bottom++ = 0;
    char *cr = strchr(bottom, '\r');
    if (cr) {
        *cr = 0;
    }
    taskENTER_CRITICAL(&s_state_lock);
    strlcpy(s_presence, top, sizeof(s_presence));
    strlcpy(s_room, bottom, sizeof(s_room));
    s_state_at_us = esp_timer_get_time();
    taskEXIT_CRITICAL(&s_state_lock);
}

#if CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG || CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
/* The board's native "USB" port. The console already writes the CSI lines out of it; this only empties its receive FIFO
 * every 20 ms with the low-level read, so no driver is installed and the output path is untouched. */
static void state_usb_task(void *arg)
{
    static state_reader_t r;
    uint8_t buf[64];
    for (;;) {
        while (usb_serial_jtag_ll_rxfifo_data_available()) {
            uint32_t n = usb_serial_jtag_ll_read_rxfifo(buf, sizeof(buf));
            for (uint32_t i = 0; i < n; i++) {
                state_feed(&r, buf[i]);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}
#endif

#if CONFIG_ESP_CONSOLE_UART
/* The board's "COM"/"UART" port. Output keeps using the normal console path; only receiving goes through the driver. */
static void state_rx_task(void *arg)
{
    static state_reader_t r;
    uint8_t c;
    for (;;) {
        if (uart_read_bytes(CONFIG_ESP_CONSOLE_UART_NUM, &c, 1, portMAX_DELAY) == 1) {
            state_feed(&r, c);
        }
    }
}
#endif

static void display_task(void *arg)
{
    char line[24], presence[17], room[17];
    uint32_t last = 0;
    for (;;) {
        uint32_t acc = s_accepted;
        taskENTER_CRITICAL(&s_state_lock);
        memcpy(presence, s_presence, sizeof(presence));
        memcpy(room, s_room, sizeof(room));
        int64_t at = s_state_at_us;
        taskEXIT_CRITICAL(&s_state_lock);
        bool pc_ok = at && (esp_timer_get_time() - at) < 10 * 1000000LL;

        oled_clear();
        snprintf(line, sizeof(line), "WIFI SENSE  RX  CH%d", WIFISENSE_CHANNEL);
        oled_text(0, 0, line);
        snprintf(line, sizeof(line), "CSI %lu/s  RSSI %d", (unsigned long)((acc - last) * 2), acc ? s_last_rssi : 0);
        oled_text(1, 0, line);
        snprintf(line, sizeof(line), "dropped %lu", (unsigned long)s_dropped);
        oled_text(2, 0, line);
        oled_hline(3);
        oled_text(4, 0, pc_ok ? presence : (at ? "PC LINK LOST" : presence));
        if (pc_ok && room[0]) {
            if (strlen(room) <= 10) {
                oled_text_big(5, 0, room);
            } else {
                oled_text(5, 0, room);
            }
        }
        oled_text(7, 0, acc == last ? "no frames from TX" : (pc_ok ? "bridge connected" : "start the bridge"));
        oled_flush();
        last = acc;
        vTaskDelay(pdMS_TO_TICKS(500));
    }
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

#if CONFIG_WIFISENSE_OLED_ENABLE
    if (oled_init(CONFIG_WIFISENSE_OLED_SDA, CONFIG_WIFISENSE_OLED_SCL)) {
#if CONFIG_ESP_CONSOLE_UART
        if (uart_driver_install(CONFIG_ESP_CONSOLE_UART_NUM, 1024, 0, 0, NULL, 0) == ESP_OK) {
            xTaskCreate(state_rx_task, "ws_state", 3072, NULL, tskIDLE_PRIORITY + 1, NULL);
        }
#endif
#if CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG || CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
        xTaskCreate(state_usb_task, "ws_state_usb", 3072, NULL, tskIDLE_PRIORITY + 1, NULL);
#endif
        xTaskCreate(display_task, "oled", 3072, NULL, tskIDLE_PRIORITY + 1, NULL);
    }
#endif

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
