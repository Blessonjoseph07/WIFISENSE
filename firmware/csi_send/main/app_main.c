/*
 * Wi-Fi Sense CSI transmitter (ESP32-S3).
 *
 * It only transmits: ~100 ESP-NOW broadcast frames per second from a fixed source MAC so the receiver can measure the
 * channel. It never talks to the API. An optional SSD1306 OLED (see components/wifisense_oled) shows that it is sending.
 *
 * Radio configuration required by the API's detector (see docs/firmware_contract.md):
 *   - 20 MHz channel (HT20, no secondary channel),
 *   - frames sent as legacy OFDM at 6 Mbps (802.11g). Not DSSS (no CSI) and not HT/HT40 (different CSI layout).
 * Derived from Espressif's esp-csi csi_send example (Apache-2.0 / CC0).
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include "nvs_flash.h"
#include "esp_mac.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_now.h"
#include "esp_idf_version.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "wifisense_oled.h"

/* IDF 6 renamed WIFI_BW_HT20 to WIFI_BW20. */
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(6, 0, 0)
#define WS_BW_20MHZ WIFI_BW20
#else
#define WS_BW_20MHZ WIFI_BW_HT20
#endif

#define WIFISENSE_CHANNEL     11     /* must be the same on the receiver */
#define SEND_FREQUENCY_HZ     100

static const uint8_t TX_MAC[6] = {0x1a, 0x00, 0x00, 0x00, 0x00, 0x00};
static const char *TAG = "wifisense_tx";
static volatile uint32_t s_sent, s_errors;

/* Refreshes the display twice a second; runs at low priority so it never delays a frame. */
static void display_task(void *arg)
{
    char line[24];
    uint32_t last = 0;
    for (;;) {
        uint32_t sent = s_sent;
        uint32_t up = (uint32_t)(esp_timer_get_time() / 1000000);
        oled_clear();
        snprintf(line, sizeof(line), "WIFI SENSE  TX  CH%d", WIFISENSE_CHANNEL);
        oled_text(0, 0, line);
        oled_hline(1);
        oled_text_big(2, 0, s_errors > sent / 10 + 5 ? "SEND ERR" : "SENDING");
        snprintf(line, sizeof(line), "frames %lu", (unsigned long)sent);
        oled_text(4, 0, line);
        snprintf(line, sizeof(line), "rate %lu/s  6 Mbps", (unsigned long)((sent - last) * 2));
        oled_text(5, 0, line);
        snprintf(line, sizeof(line), "send errors %lu", (unsigned long)s_errors);
        oled_text(6, 0, line);
        snprintf(line, sizeof(line), "up %02lu:%02lu:%02lu", (unsigned long)(up / 3600), (unsigned long)(up / 60 % 60), (unsigned long)(up % 60));
        oled_text(7, 0, line);
        oled_flush();
        last = sent;
        vTaskDelay(pdMS_TO_TICKS(500));
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
    ESP_ERROR_CHECK(esp_wifi_set_mac(WIFI_IF_STA, TX_MAC));
}

static void esp_now_setup(const esp_now_peer_info_t *peer)
{
    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_set_pmk((const uint8_t *)"pmk1234567890123"));
    ESP_ERROR_CHECK(esp_now_add_peer(peer));
    esp_now_rate_config_t rate = {
        .phymode = WIFI_PHY_MODE_11G,    /* legacy OFDM: carries the legacy long training field only */
        .rate    = WIFI_PHY_RATE_6M,
        .ersu    = false,
        .dcm     = false,
    };
    ESP_ERROR_CHECK(esp_now_set_peer_rate_config(peer->peer_addr, &rate));
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

    esp_now_peer_info_t peer = {
        .channel   = WIFISENSE_CHANNEL,
        .ifidx     = WIFI_IF_STA,
        .encrypt   = false,
        .peer_addr = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
    };
    esp_now_setup(&peer);

#if CONFIG_WIFISENSE_OLED_ENABLE
    if (oled_init(CONFIG_WIFISENSE_OLED_SDA, CONFIG_WIFISENSE_OLED_SCL)) {
        xTaskCreate(display_task, "oled", 3072, NULL, tskIDLE_PRIORITY + 1, NULL);
    }
#endif

    ESP_LOGI(TAG, "TX ready: channel %d HT20, legacy OFDM 6 Mbps, %d frames/s, source MAC " MACSTR,
             WIFISENSE_CHANNEL, SEND_FREQUENCY_HZ, MAC2STR(TX_MAC));

    for (uint32_t count = 0;; ++count) {
        esp_err_t err = esp_now_send(peer.peer_addr, (const uint8_t *)&count, sizeof(count));
        if (err != ESP_OK) {
            s_errors++;
            ESP_LOGW(TAG, "send error <%s>", esp_err_to_name(err));
        } else {
            s_sent++;
        }
        usleep(1000 * 1000 / SEND_FREQUENCY_HZ);
    }
}
