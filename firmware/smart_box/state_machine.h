#pragma once

#include <Arduino.h>

#include "buzzer.h"
#include "camera.h"
#include "display.h"
#include "net.h"
#include "pcf8575.h"
#include "rfid.h"

enum class BoxState {
  BOOT,
  AVAILABLE,
  DOOR_UNLOCKED,
  DEPOSIT_VERIFY,
  PICKUP_WAIT,
  PICKUP_VERIFY,
  ERROR
};

struct SmartBoxContext {
  SmartBoxNetwork *network;
  SmartBoxDisplay *display;
  PcF8575Driver *expander;
  SmartBoxRfid *rfid;
  SmartBoxCamera *camera;
  SmartBoxBuzzer *buzzer;
};

class SmartBoxStateMachine {
 public:
  void begin(const SmartBoxContext &ctx);
  void loop();

 private:
  void transitionTo(BoxState state);
  void handleBoot();
  void handleAvailable();
  void handleDoorUnlocked();
  void handleDepositVerify();
  void handlePickupWait();
  void handlePickupVerify();
  void handleError();
  void captureAndUpload(const String &event, const String &status);

  SmartBoxContext ctx_{};
  BoxState state_ = BoxState::BOOT;
  uint32_t stateEnterMs_ = 0;
  uint32_t relayEngagedMs_ = 0;
  uint32_t lastSnapshotMs_ = 0;
  uint32_t lastIrTriggerMs_ = 0;
  bool relayClosed_ = false;
};

