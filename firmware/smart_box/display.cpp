#include "display.h"

#include <SPI.h>
#ifdef ARDUINO_ARCH_ESP8266
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#endif

#include "config.h"

namespace {
#ifdef ARDUINO_ARCH_ESP8266
Adafruit_ST7735 tft = Adafruit_ST7735(SmartBoxConfig::kSpiCsDisplayPin, -1, -1);
#endif
}

void SmartBoxDisplay::begin() {
#ifdef ARDUINO_ARCH_ESP8266
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextWrap(true);
  tft.setTextColor(ST77XX_WHITE);
#endif
}

void SmartBoxDisplay::showBoot() {
#ifdef ARDUINO_ARCH_ESP8266
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(10, 40);
  tft.setTextSize(2);
  tft.print(F("Booting..."));
#else
  Serial.println(F("[DISPLAY] Booting..."));
#endif
}

void SmartBoxDisplay::drawQr(const String &text) {
#if defined(QRCODE_H) || defined(QRCODEGEN_H)
  QRCode qrcode;
  uint8_t qrcodeData[qrcode_getBufferSize(3)];
  qrcode_initText(&qrcode, qrcodeData, 3, ECC_MEDIUM, text.c_str());
#ifdef ARDUINO_ARCH_ESP8266
  const uint8_t scale = 3;
  const uint16_t offsetX = 10;
  const uint16_t offsetY = 10;
  tft.fillScreen(ST77XX_BLACK);
  for (uint8_t y = 0; y < qrcode.size; ++y) {
    for (uint8_t x = 0; x < qrcode.size; ++x) {
      if (qrcode_getModule(&qrcode, x, y)) {
        tft.fillRect(offsetX + x * scale, offsetY + y * scale, scale, scale,
                     ST77XX_WHITE);
      }
    }
  }
#endif
#else
  (void)text;
#endif
}

void SmartBoxDisplay::showAvailable(const String &boxId) {
  String url = String(F("/upload-page?box_id=")) + boxId;
  drawQr(url);
#ifdef ARDUINO_ARCH_ESP8266
  tft.setCursor(0, 110);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_GREEN);
  tft.println(F("Scan QR to deposit"));
  tft.println(url);
#else
  Serial.print(F("[DISPLAY] Available: "));
  Serial.println(url);
#endif
}

void SmartBoxDisplay::showStatus(const String &message) {
#ifdef ARDUINO_ARCH_ESP8266
  tft.fillRect(0, 120, 160, 40, ST77XX_BLACK);
  tft.setCursor(0, 120);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1);
  tft.println(message);
#else
  Serial.print(F("[DISPLAY] "));
  Serial.println(message);
#endif
}

void SmartBoxDisplay::showError(const String &error) {
#ifdef ARDUINO_ARCH_ESP8266
  tft.fillRect(0, 120, 160, 40, ST77XX_BLACK);
  tft.setCursor(0, 120);
  tft.setTextColor(ST77XX_RED);
  tft.setTextSize(1);
  tft.println(error);
#else
  Serial.print(F("[DISPLAY][ERR] "));
  Serial.println(error);
#endif
}

