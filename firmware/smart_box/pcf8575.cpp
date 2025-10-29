#include "pcf8575.h"

#include "config.h"

namespace {
constexpr uint8_t kPrimaryFirst = 0x20;
constexpr uint8_t kPrimaryLast = 0x27;
constexpr uint8_t kSecondaryFirst = 0x38;
constexpr uint8_t kSecondaryLast = 0x3F;
}

bool PcF8575Driver::begin(TwoWire &wire) {
  wire_ = &wire;
  wire_->begin(SmartBoxConfig::kI2cSdaPin, SmartBoxConfig::kI2cSclPin);

  if (!probeAddressRange(wire, kPrimaryFirst, kPrimaryLast) &&
      !probeAddressRange(wire, kSecondaryFirst, kSecondaryLast)) {
    Serial.println(F("[PCF8575] No expander detected"));
    return false;
  }

  // Ensure outputs default high and capture initial shadow.
  writePin(SmartBoxConfig::kPcfRelayBit, false);
  read16();
  return true;
}

bool PcF8575Driver::probeAddressRange(TwoWire &wire, uint8_t first, uint8_t last) {
  for (uint8_t addr = first; addr <= last; ++addr) {
    wire.beginTransmission(addr);
    if (wire.endTransmission() == 0) {
      address_ = addr;
      Serial.print(F("[PCF8575] Using address 0x"));
      Serial.println(addr, HEX);
      return true;
    }
  }
  return false;
}

uint16_t PcF8575Driver::read16() {
  if (!wire_ || address_ == 0) {
    return shadow_;
  }

  if (!readOnce(&shadow_)) {
    Serial.println(F("[PCF8575] Read failed"));
  }
  return shadow_;
}

bool PcF8575Driver::readOnce(uint16_t *value) {
  wire_->requestFrom(address_, static_cast<uint8_t>(2));
  if (wire_->available() < 2) {
    return false;
  }
  uint8_t low = wire_->read();
  uint8_t high = wire_->read();
  *value = static_cast<uint16_t>(high << 8 | low);
  return true;
}

bool PcF8575Driver::readPin(uint8_t bit, bool *value, uint32_t now) {
  (void)now;
  uint16_t data = read16();
  bool level = data & (1 << bit);
  if (value) {
    *value = level;
  }
  return level;
}

void PcF8575Driver::writePin(uint8_t bit, bool level) {
  if (!wire_ || address_ == 0) {
    return;
  }
  if (level) {
    shadow_ |= (1 << bit);
  } else {
    shadow_ &= ~(1 << bit);
  }
  wire_->beginTransmission(address_);
  wire_->write(static_cast<uint8_t>(shadow_ & 0xFF));
  wire_->write(static_cast<uint8_t>((shadow_ >> 8) & 0xFF));
  if (wire_->endTransmission() != 0) {
    Serial.println(F("[PCF8575] Write failed"));
  }
}

void PcF8575Driver::relay_close() {
  writePin(SmartBoxConfig::kPcfRelayBit, true);
}

void PcF8575Driver::relay_open() {
  writePin(SmartBoxConfig::kPcfRelayBit, false);
}

bool PcF8575Driver::doorButtonPressed(uint32_t now) {
  bool raw = readPin(SmartBoxConfig::kPcfDoorButtonBit, nullptr, now) == 0;
  DebounceState &debounce = doorDebounce_;

  if (now - debounce.lastCheck > SmartBoxConfig::kDebounceIntervalMs) {
    bool stable = (raw == debounce.lastValue);
    debounce.lastCheck = now;
    if (stable) {
      debounce.stableReads++;
    } else {
      debounce.stableReads = 1;
      debounce.lastValue = raw;
    }
  }
  return debounce.stableReads >= SmartBoxConfig::kDebounceStableReads &&
         debounce.lastValue;
}

bool PcF8575Driver::irBeamBroken(uint32_t now) {
  bool raw = readPin(SmartBoxConfig::kPcfIrSensorBit, nullptr, now) == 0;
  DebounceState &debounce = irDebounce_;
  if (now - debounce.lastCheck > SmartBoxConfig::kDebounceIntervalMs) {
    bool stable = (raw == debounce.lastValue);
    debounce.lastCheck = now;
    if (stable) {
      debounce.stableReads++;
    } else {
      debounce.stableReads = 1;
      debounce.lastValue = raw;
    }
  }
  return debounce.stableReads >= SmartBoxConfig::kDebounceStableReads &&
         debounce.lastValue;
}

