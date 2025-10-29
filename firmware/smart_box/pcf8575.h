#pragma once

#include <Wire.h>
#include <Arduino.h>

class PcF8575Driver {
 public:
  bool begin(TwoWire &wire = Wire);

  uint16_t read16();
  bool readPin(uint8_t bit, bool *value, uint32_t now);
  void writePin(uint8_t bit, bool level);

  void relay_close();
  void relay_open();

  bool doorButtonPressed(uint32_t now);
  bool irBeamBroken(uint32_t now);

 private:
  bool probeAddressRange(TwoWire &wire, uint8_t first, uint8_t last);
  bool readOnce(uint16_t *value);

  uint8_t address_ = 0;
  uint16_t shadow_ = 0xFFFF;  // PCF8575 defaults to HIGH
  TwoWire *wire_ = nullptr;

  struct DebounceState {
    uint32_t lastCheck = 0;
    uint16_t stableReads = 0;
    bool lastValue = false;
  } irDebounce_, doorDebounce_;
};

