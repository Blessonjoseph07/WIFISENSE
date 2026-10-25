/*
 * Minimal SSD1306 128x64 I2C OLED driver for the Wi-Fi Sense boards (0.96-inch modules, address 0x3C or 0x3D).
 *
 * Optional by design: oled_init() returns false when no display answers, and every other call is then a no-op,
 * so a board without a display (or with a loose wire) keeps sensing exactly as before.
 *
 * Text grid: 8 rows x 21 columns with the built-in 5x7 font; oled_text_big() draws at 2x (4 rows x 10 columns).
 * Draw into the frame buffer, then call oled_flush() once to send it.
 */
#pragma once

#include <stdbool.h>

bool oled_init(int sda_gpio, int scl_gpio);
bool oled_present(void);
void oled_clear(void);
void oled_text(int row, int col, const char *s);       /* row 0..7, col 0..20 */
void oled_text_big(int row, int col, const char *s);   /* row 0..6 (uses row and row+1), col 0..9 */
void oled_hline(int row);                              /* thin line through the middle of a text row */
void oled_pixel(int x, int y);                         /* one pixel on, x 0..127, y 0..63 (off-screen is ignored) */
void oled_flush(void);
