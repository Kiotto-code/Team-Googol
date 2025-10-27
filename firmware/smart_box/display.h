#pragma once

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <qrcode.h>

#include "config.h"

class Display {
public:
  Display() : _tft(nullptr), _spi(nullptr), _cs(0) {}

  void begin(SPIClass &spi) {
    _spi = &spi;
    static Adafruit_ST7735 tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_RST);
    _tft = &tft;
    _spi->begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);
    pinMode(PIN_TFT_CS, OUTPUT);
    pinMode(PIN_TFT_DC, OUTPUT);
    pinMode(PIN_TFT_RST, OUTPUT);
    digitalWrite(PIN_TFT_CS, HIGH);
    _tft->initR(INITR_BLACKTAB);
    _tft->setRotation(1); // Landscape
    _tft->fillScreen(DISPLAY_BG_COLOR);
    _tft->setTextWrap(true);
    showBoot();
  }

  void showBoot() { drawMessage("Smart Box", "Booting..."); }
  void showReady() { showQrForUpload(); }
  void showOffline() { drawMessage("Offline", "Service unavailable"); }
  void showSession(const String &line1, const String &line2) {
    drawMessage(line1, line2);
  }
  void showError(const String &line) { drawMessage("Error", line); }
  void showInfo(const String &line) { drawMessage("Info", line); }

  void showQrForUpload() {
    if (!_tft) {
      return;
    }
    String url = String(SERVER_BASE_URL) + "/upload-page?box_id=" + BOX_ID;

    QRCode qrcode;
    uint8_t qrcodeData[qrcode_getBufferSize(3)];
    if (qrcode_initText(&qrcode, qrcodeData, 3, ECC_MEDIUM, url.c_str()) == 0) {
      digitalWrite(PIN_TFT_CS, LOW);
      _tft->fillScreen(DISPLAY_BG_COLOR);
      const uint8_t scale = 4;
      int offsetX = (_tft->width() - qrcode.size * scale) / 2;
      int offsetY = (_tft->height() - qrcode.size * scale) / 2;
      for (uint8_t y = 0; y < qrcode.size; ++y) {
        for (uint8_t x = 0; x < qrcode.size; ++x) {
          uint16_t color = qrcode_getModule(&qrcode, x, y) ? ST77XX_WHITE : ST77XX_BLACK;
          _tft->fillRect(offsetX + x * scale, offsetY + y * scale, scale, scale, color);
        }
      }
      _tft->setCursor(0, 0);
      _tft->setTextColor(ST77XX_GREEN);
      _tft->setTextSize(1);
      _tft->println("Upload label");
      _tft->setCursor(4, _tft->height() - 12);
      _tft->setTextColor(ST77XX_YELLOW);
      _tft->println("Tap card to start");
      digitalWrite(PIN_TFT_CS, HIGH);
    } else {
      drawMessage("Scan URL", url);
    }
  }

private:
  void drawMessage(const String &title, const String &body) {
    if (!_tft) {
      return;
    }
    digitalWrite(PIN_TFT_CS, LOW);
    _tft->fillScreen(DISPLAY_BG_COLOR);
    _tft->setTextColor(DISPLAY_TEXT_COLOR);
    _tft->setTextSize(2);
    _tft->setCursor(4, 4);
    _tft->println(title);
    _tft->setTextSize(1);
    _tft->setCursor(4, 34);
    _tft->println(body);
    digitalWrite(PIN_TFT_CS, HIGH);
  }

  Adafruit_ST7735 *_tft;
  SPIClass *_spi;
  uint8_t _cs;
};
