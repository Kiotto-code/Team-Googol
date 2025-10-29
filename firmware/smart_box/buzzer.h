#pragma once

#include <Arduino.h>

class SmartBoxBuzzer {
 public:
  explicit SmartBoxBuzzer(uint8_t pin) : pin_(pin) {}

  void begin();
  void patternWarn();
  void patternTimeout();
  void silent();

 private:
  void toneBurst(uint16_t frequency, uint16_t durationMs);
  uint8_t pin_;
};

