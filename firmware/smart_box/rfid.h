#pragma once

#include <Arduino.h>
#include <MFRC522.h>

#include <array>

class SmartBoxRfid {
 public:
  SmartBoxRfid(uint8_t ssPin, uint8_t rstPin) : rfid_(ssPin, rstPin) {}

  void begin();
  bool readUidOnce(uint32_t timeoutMs, String *uidOut);
  void loop();

 private:
  MFRC522 rfid_;
  uint32_t lastUidMs_ = 0;
  String lastUid_;
};

