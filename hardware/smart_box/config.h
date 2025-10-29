#pragma once

#include <Arduino.h>

// Unique identifier for this smart box installation.
constexpr const char *BOX_ID = "SMART_BOX_001";

// Wi-Fi credentials used by the prototype firmware.
constexpr const char *WIFI_SSID = "HONOR";
constexpr const char *WIFI_PASSWORD = "12345678";

// GPIO assignments for the ESP32-S3 based hardware build.
constexpr uint8_t PIN_RELAY = 6;            // Relay coil driver
constexpr uint8_t PIN_BUZZER = 7;           // Passive buzzer pin
constexpr uint8_t PIN_DOOR_SENSOR = 4;      // Door contact switch (LOW = closed)
constexpr uint8_t PIN_IR_SENSOR = 5;        // IR beam sensor for parcel detection
constexpr uint8_t PIN_STATUS_LED = 15;      // Status LED for visual feedback
constexpr uint8_t PIN_PCF8575_INT = 16;     // Interrupt line from PCF8575

constexpr int PIN_I2C1_SDA = 17;
constexpr int PIN_I2C1_SCL = 18;

constexpr int PIN_SPI_SCK = 12;
constexpr int PIN_SPI_MISO = 13;
constexpr int PIN_SPI_MOSI = 11;

constexpr uint8_t PIN_TFT_CS = 21;
constexpr uint8_t PIN_TFT_DC = 47;
constexpr uint8_t PIN_TFT_RST = 41;

constexpr uint8_t PIN_RFID_SS = 1;
constexpr uint8_t PIN_RFID_RST = 42;

constexpr uint8_t RELAY_ACTIVE_LEVEL = HIGH;

constexpr uint32_t WIFI_BOOT_TIMEOUT_MS = 15000;    // 15 s boot fallback
constexpr uint32_t DOOR_OPEN_ALERT_MS = 30000;      // 30 s door-open alert
constexpr uint32_t RELAY_RELEASE_MS = 5000;         // 5 s automatic relay release
constexpr uint32_t IR_SNAPSHOT_INTERVAL_MS = 20000; // >=20 s between snapshots
constexpr uint32_t RFID_DEBOUNCE_MS = 2000;         // Ignore repeated tags within 2 s
constexpr uint32_t NETWORK_REQUEST_TIMEOUT_MS = 7000; // 7 s network call timeout

constexpr const char *SERVER_BASE_URL = "http://localhost:8000";
constexpr const char *ENDPOINT_EVENT_LOG = "/api/box/event";
constexpr const char *ENDPOINT_RFID_LOOKUP = "/api/box/lookup";
constexpr const char *ENDPOINT_UPLOAD = "/api/box/upload";

constexpr uint16_t DISPLAY_BG_COLOR = 0x0000;   // Black
constexpr uint16_t DISPLAY_TEXT_COLOR = 0xFFFF; // White
