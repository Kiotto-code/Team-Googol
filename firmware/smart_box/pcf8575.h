#pragma once

#include <Arduino.h>
#include <Wire.h>

class Pcf8575Expander {
public:
  Pcf8575Expander() : _address(0), _shadow(0xFFFF), _wire(nullptr), _present(false) {}

  bool begin(TwoWire &wire) {
    _wire = &wire;
    _present = false;
    static const uint8_t primaryRangeStart = 0x20;
    static const uint8_t primaryRangeEnd = 0x27;
    static const uint8_t secondaryRangeStart = 0x38;
    static const uint8_t secondaryRangeEnd = 0x3F;

    for (uint8_t addr = primaryRangeStart; addr <= primaryRangeEnd; ++addr) {
      if (probeAddress(addr)) {
        _address = addr;
        _present = true;
        break;
      }
    }
    if (!_present) {
      for (uint8_t addr = secondaryRangeStart; addr <= secondaryRangeEnd; ++addr) {
        if (probeAddress(addr)) {
          _address = addr;
          _present = true;
          break;
        }
      }
    }

    if (_present) {
      // Default all pins HIGH (inputs)
      writeShadow(0xFFFF);
    }
    return _present;
  }

  bool isPresent() const { return _present; }
  uint8_t address() const { return _address; }

  void digitalWrite(uint8_t pin, bool level) {
    if (!_present || pin > 15) {
      return;
    }
    if (level) {
      _shadow |= (1u << pin);
    } else {
      _shadow &= ~(1u << pin);
    }
    writeShadow(_shadow);
  }

  bool digitalRead(uint8_t pin) {
    if (!_present || pin > 15) {
      return false;
    }
    updateShadow();
    return (_shadow >> pin) & 0x01;
  }

  uint16_t shadow() const { return _shadow; }

private:
  bool probeAddress(uint8_t addr) {
    _wire->beginTransmission(addr);
    return _wire->endTransmission() == 0;
  }

  void updateShadow() {
    if (!_present) {
      return;
    }
    _wire->beginTransmission(_address);
    if (_wire->endTransmission() != 0) {
      _present = false;
      return;
    }
    _wire->requestFrom((int)_address, 2);
    if (_wire->available() == 2) {
      uint8_t lo = _wire->read();
      uint8_t hi = _wire->read();
      _shadow = static_cast<uint16_t>(hi << 8 | lo);
    }
  }

  void writeShadow(uint16_t value) {
    if (!_present) {
      return;
    }
    _wire->beginTransmission(_address);
    _wire->write(value & 0xFF);
    _wire->write(value >> 8);
    if (_wire->endTransmission() != 0) {
      _present = false;
    }
  }

  uint8_t _address;
  uint16_t _shadow;
  TwoWire *_wire;
  bool _present;
};
