#pragma once

#include <Arduino.h>

namespace SmartBoxConfig {

// Wi-Fi credentials
static constexpr const char *kWifiSsid = "HONOR";
static constexpr const char *kWifiPassword = "12345678";

// Unique identifier for this smart box
static constexpr const char *kBoxId = "route-a-locker-01";

// GPIO pin map
static constexpr uint8_t kI2cSdaPin = 2;   // GPIO2
static constexpr uint8_t kI2cSclPin = 14;  // GPIO14

// SPI Pins (ESP8266-style defaults)
static constexpr uint8_t kSpiMisoPin = 12;
static constexpr uint8_t kSpiMosiPin = 13;
static constexpr uint8_t kSpiSckPin = 14;
static constexpr uint8_t kSpiCsDisplayPin = 15;
static constexpr uint8_t kSpiCsRfidPin = 4;
static constexpr uint8_t kSpiCsCameraPin = 5;

// PCF8575 bit assignments (P00..P17)
static constexpr uint8_t kPcfIrSensorBit = 0;      // P00
static constexpr uint8_t kPcfDoorButtonBit = 3;    // P03
static constexpr uint8_t kPcfDoorClosedBit = 4;    // P04
static constexpr uint8_t kPcfRelayBit = 8;         // P10 (HIGH active)
static constexpr uint8_t kPcfStatusLedBit = 12;    // P14 equivalent on upper byte

// Debounce and sampling parameters
static constexpr uint16_t kDebounceStableReads = 5;
static constexpr uint32_t kDebounceIntervalMs = 20;
static constexpr uint32_t kRfidDeduplicateMs = 2000;
static constexpr uint32_t kSnapshotIntervalMs = 20000;

// Timing constants
static constexpr uint32_t kDoorTimeoutMs = 30000;
static constexpr uint32_t kRelaySafetyMs = 5000;
static constexpr uint32_t kWifiConnectTimeoutMs = 15000;
static constexpr uint32_t kHttpRequestTimeoutMs = 7000;

}  // namespace SmartBoxConfig
