#pragma once

#include <Arduino.h>
#include <MFRC522.h>

#include "config.h"

class RfidReader {
public:
  RfidReader() : _reader(PIN_RFID_SS, PIN_RFID_RST), _spi(nullptr), _lastUid(""), _lastReadMs(0) {}

  void begin(SPIClass &spi) {
    _spi = &spi;
    pinMode(PIN_RFID_SS, OUTPUT);
    digitalWrite(PIN_RFID_SS, HIGH);
    pinMode(PIN_RFID_RST, OUTPUT);
    digitalWrite(PIN_RFID_RST, HIGH);
    _reader.PCD_Init();
  }

  bool poll(uint32_t now, String &uidOut) {
    if (!_spi) {
      return false;
    }
    digitalWrite(PIN_TFT_CS, HIGH); // ensure TFT deselected
    digitalWrite(PIN_RFID_SS, LOW);
    bool result = false;
    if (_reader.PICC_IsNewCardPresent() && _reader.PICC_ReadCardSerial()) {
      uidOut = uidToString(_reader.uid);
      if (now - _lastReadMs > RFID_DEBOUNCE_MS || uidOut != _lastUid) {
        _lastUid = uidOut;
        _lastReadMs = now;
        result = true;
      }
      _reader.PICC_HaltA();
      _reader.PCD_StopCrypto1();
    }
    digitalWrite(PIN_RFID_SS, HIGH);
    return result;
  }

  void powerDown() {
    _reader.PCD_AntennaOff();
  }

private:
  static String uidToString(MFRC522::Uid &uid) {
    String value;
    for (byte i = 0; i < uid.size; ++i) {
      if (uid.uidByte[i] < 0x10) {
        value += "0";
      }
      value += String(uid.uidByte[i], HEX);
    }
    value.toUpperCase();
    return value;
  }

  MFRC522 _reader;
  SPIClass *_spi;
  String _lastUid;
  uint32_t _lastReadMs;
};
