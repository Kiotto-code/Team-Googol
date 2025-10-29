#include "state_machine.h"

#include "config.h"
#include <ESP8266WiFi.h>

namespace {
bool isDoorClosed(PcF8575Driver *expander) {
  bool level = false;
  expander->readPin(SmartBoxConfig::kPcfDoorClosedBit, &level, millis());
  return level;
}

String makeJson(const String &event, const String &extra) {
  String json = String(F("{\"box_id\":\"")) + SmartBoxConfig::kBoxId +
                F("\",\"event\":\"") + event + F("\"");
  if (extra.length()) {
    json += F(",") + extra;
  }
  json += F("}");
  return json;
}
}

void SmartBoxStateMachine::begin(const SmartBoxContext &ctx) {
  ctx_ = ctx;
  state_ = BoxState::BOOT;
  stateEnterMs_ = millis();
  ctx_.display->showBoot();
  transitionTo(BoxState::BOOT);
}

void SmartBoxStateMachine::transitionTo(BoxState state) {
  state_ = state;
  stateEnterMs_ = millis();
  Serial.print(F("[STATE] -> "));
  Serial.println(static_cast<int>(state));
  switch (state_) {
    case BoxState::BOOT:
      ctx_.display->showBoot();
      break;
    case BoxState::AVAILABLE:
      ctx_.display->showAvailable(SmartBoxConfig::kBoxId);
      ctx_.buzzer->silent();
      break;
    case BoxState::DOOR_UNLOCKED:
      ctx_.display->showStatus(F("Door unlocked"));
      break;
    case BoxState::DEPOSIT_VERIFY:
      ctx_.display->showStatus(F("Verifying deposit"));
      break;
    case BoxState::PICKUP_WAIT:
      ctx_.display->showStatus(F("Pickup in progress"));
      break;
    case BoxState::PICKUP_VERIFY:
      ctx_.display->showStatus(F("Verifying pickup"));
      break;
    case BoxState::ERROR:
      ctx_.display->showError(F("Door timeout"));
      ctx_.buzzer->patternTimeout();
      break;
  }
}

void SmartBoxStateMachine::loop() {
  switch (state_) {
    case BoxState::BOOT:
      handleBoot();
      break;
    case BoxState::AVAILABLE:
      handleAvailable();
      break;
    case BoxState::DOOR_UNLOCKED:
      handleDoorUnlocked();
      break;
    case BoxState::DEPOSIT_VERIFY:
      handleDepositVerify();
      break;
    case BoxState::PICKUP_WAIT:
      handlePickupWait();
      break;
    case BoxState::PICKUP_VERIFY:
      handlePickupVerify();
      break;
    case BoxState::ERROR:
      handleError();
      break;
  }

  if (relayClosed_ && millis() - relayEngagedMs_ > SmartBoxConfig::kRelaySafetyMs) {
    ctx_.expander->relay_open();
    relayClosed_ = false;
  }
}

void SmartBoxStateMachine::handleBoot() {
  if (ctx_.network->ensureWifi()) {
    transitionTo(BoxState::AVAILABLE);
  } else if (millis() - stateEnterMs_ > SmartBoxConfig::kWifiConnectTimeoutMs) {
    transitionTo(BoxState::ERROR);
  }
}

void SmartBoxStateMachine::handleAvailable() {
  uint32_t now = millis();
  ctx_.network->ensureWifi(0);
  if (ctx_.expander->doorButtonPressed(now)) {
    ctx_.expander->relay_close();
    relayClosed_ = true;
    relayEngagedMs_ = now;
    ctx_.buzzer->patternWarn();
    transitionTo(BoxState::DOOR_UNLOCKED);
    return;
  }

  String uid;
  if (ctx_.rfid->readUidOnce(50, &uid)) {
    Serial.print(F("[RFID] Card: "));
    Serial.println(uid);
    ctx_.expander->relay_close();
    relayClosed_ = true;
    relayEngagedMs_ = now;
    transitionTo(BoxState::PICKUP_WAIT);
    return;
  }

  if (ctx_.expander->irBeamBroken(now) && now - lastIrTriggerMs_ > SmartBoxConfig::kSnapshotIntervalMs) {
    lastIrTriggerMs_ = now;
    transitionTo(BoxState::DEPOSIT_VERIFY);
  }
}

void SmartBoxStateMachine::handleDoorUnlocked() {
  uint32_t now = millis();
  if (millis() - stateEnterMs_ > SmartBoxConfig::kDoorTimeoutMs) {
    ctx_.buzzer->patternTimeout();
    transitionTo(BoxState::ERROR);
    return;
  }
  if (isDoorClosed(ctx_.expander)) {
    transitionTo(BoxState::DEPOSIT_VERIFY);
  }
}

void SmartBoxStateMachine::handleDepositVerify() {
  uint32_t now = millis();
  if (now - lastSnapshotMs_ < SmartBoxConfig::kSnapshotIntervalMs && state_ == BoxState::DEPOSIT_VERIFY) {
    transitionTo(BoxState::AVAILABLE);
    return;
  }

  lastSnapshotMs_ = now;
  captureAndUpload(F("deposit"), F("captured"));
  transitionTo(BoxState::AVAILABLE);
}

void SmartBoxStateMachine::handlePickupWait() {
  uint32_t now = millis();
  if (now - stateEnterMs_ > SmartBoxConfig::kDoorTimeoutMs) {
    ctx_.buzzer->patternTimeout();
    transitionTo(BoxState::ERROR);
    return;
  }
  if (isDoorClosed(ctx_.expander)) {
    transitionTo(BoxState::PICKUP_VERIFY);
  }
}

void SmartBoxStateMachine::handlePickupVerify() {
  uint32_t now = millis();
  if (now - lastSnapshotMs_ < SmartBoxConfig::kSnapshotIntervalMs && state_ == BoxState::PICKUP_VERIFY) {
    transitionTo(BoxState::AVAILABLE);
    return;
  }
  lastSnapshotMs_ = now;
  captureAndUpload(F("pickup"), F("verified"));
  transitionTo(BoxState::AVAILABLE);
}

void SmartBoxStateMachine::handleError() {
  ctx_.network->ensureWifi(0);
  if (isDoorClosed(ctx_.expander) && WiFi.status() == WL_CONNECTED) {
    transitionTo(BoxState::AVAILABLE);
  }
}

void SmartBoxStateMachine::captureAndUpload(const String &event, const String &status) {
  ctx_.network->ensureWifi();
  size_t totalBytes = 0;
  ctx_.camera->captureJpeg([&](const uint8_t *data, size_t len) {
    (void)data;
    totalBytes += len;
    Serial.print(F("[CAMERA] chunk bytes: "));
    Serial.println(len);
  });

  String metadata = makeJson(event, String(F("\"status\":\"")) + status +
                                      F("\",\"size\":") + String(totalBytes));
  ctx_.network->uploadSnapshot(metadata, [&](HTTPClient &client) {
    client.addHeader("Content-Type", "application/octet-stream");
    String body = String(F("JPEG-CHUNKS:")) + String(totalBytes);
    int code = client.POST(body);
    Serial.print(F("[NET] snapshot upload code "));
    Serial.println(code);
    return code >= 200 && code < 300;
  });

  ctx_.network->postEvent(String(F("/api/box/")) + event,
                          makeJson(event, String(F("\"status\":\"")) + status + F("\"")));
}

