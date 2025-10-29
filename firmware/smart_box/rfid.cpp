#include "rfid.h"

#include "config.h"

void SmartBoxRfid::begin() {
  SPI.begin();
  rfid_.PCD_Init();
}

void SmartBoxRfid::loop() {
  rfid_.PCD_AntennaOn();
}

bool SmartBoxRfid::readUidOnce(uint32_t timeoutMs, String *uidOut) {
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    if (!rfid_.PICC_IsNewCardPresent() || !rfid_.PICC_ReadCardSerial()) {
      delay(50);
      continue;
    }
    String uid;
    for (byte i = 0; i < rfid_.uid.size; ++i) {
      if (rfid_.uid.uidByte[i] < 0x10) {
        uid += '0';
      }
      uid += String(rfid_.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();

    if (millis() - lastUidMs_ < SmartBoxConfig::kRfidDeduplicateMs && uid == lastUid_) {
      return false;
    }
    lastUid_ = uid;
    lastUidMs_ = millis();

    if (uidOut) {
      *uidOut = uid;
    }
    rfid_.PICC_HaltA();
    return true;
  }
  return false;
}

