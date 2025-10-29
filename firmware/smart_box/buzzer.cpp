#include "buzzer.h"

void SmartBoxBuzzer::begin() {
  pinMode(pin_, OUTPUT);
  digitalWrite(pin_, LOW);
}

void SmartBoxBuzzer::toneBurst(uint16_t frequency, uint16_t durationMs) {
#ifdef ARDUINO_ARCH_ESP8266
  tone(pin_, frequency, durationMs);
  delay(durationMs);
#else
  (void)frequency;
  (void)durationMs;
#endif
}

void SmartBoxBuzzer::patternWarn() {
  toneBurst(2000, 120);
  delay(60);
  toneBurst(2000, 120);
}

void SmartBoxBuzzer::patternTimeout() {
  for (uint8_t i = 0; i < 3; ++i) {
    toneBurst(1500, 200);
    delay(80);
  }
}

void SmartBoxBuzzer::silent() {
  noTone(pin_);
  digitalWrite(pin_, LOW);
}

