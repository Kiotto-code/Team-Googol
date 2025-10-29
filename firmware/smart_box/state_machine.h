#pragma once

#include <Arduino.h>
#include <SPI.h>
#include <vector>

#include "camera.h"
#include "config.h"
#include "display.h"
#include "box_network.h"
#include "pcf8575.h"
#include "rfid.h"

enum class SmartBoxState { Booting, Offline, Idle, AwaitingLookup, Unlocking, DoorOpen };
enum class SessionMode { None, Deposit, Pickup };

struct SmartBoxContext {
  SmartBoxState state{SmartBoxState::Booting};
  SessionMode session{SessionMode::None};
  uint32_t bootStarted{0};
  uint32_t relayActivatedAt{0};
  uint32_t doorOpenedAt{0};
  uint32_t lastDoorChange{0};
  uint32_t lastSnapshot{0};
  uint32_t lastIrState{0};
  uint32_t lastOfflineToast{0};
  bool doorWasOpen{false};
  bool buzzerActive{false};
  bool relayActive{false};
  bool doorAlertSent{false};
  String pendingUid;
  uint32_t lookupNextAttempt{0};
  uint8_t lookupAttempts{0};
};

class SmartBoxStateMachine {
public:
  SmartBoxStateMachine(Display &display, RfidReader &rfid, CameraController &camera,
                       BoxNetworkClient &network, Pcf8575Expander &pcf)
      : _display(display), _rfid(rfid), _camera(camera), _network(network), _pcf(pcf) {}

  void begin() {
    _ctx.bootStarted = millis();
    _display.showBoot();
    _network.begin();
    _camera.begin();
    _ctx.state = SmartBoxState::Booting;
    pinMode(PIN_RELAY, OUTPUT);
    digitalWrite(PIN_RELAY, RELAY_ACTIVE_LEVEL == HIGH ? LOW : HIGH);
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);
    pinMode(PIN_DOOR_SENSOR, INPUT_PULLUP);
    pinMode(PIN_IR_SENSOR, INPUT_PULLUP);
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);
  }

  void update(uint32_t now) {
    _network.loop(now);
    handleIr(now);
    handleRelay(now);

    bool doorOpen = digitalRead(PIN_DOOR_SENSOR) == HIGH;
    if (_pcf.isPresent()) {
      _pcf.digitalWrite(0, doorOpen ? LOW : HIGH);
    }

    if (doorOpen != _ctx.doorWasOpen) {
      _ctx.doorWasOpen = doorOpen;
      _ctx.lastDoorChange = now;
      if (doorOpen) {
        _ctx.doorOpenedAt = now;
        _ctx.state = SmartBoxState::DoorOpen;
        _ctx.doorAlertSent = false;
        _display.showSession(sessionTitle(), "Door open");
        _network.logEvent("door_open", "{\"box_id\":\"" + String(BOX_ID) + "\"}");
      } else {
        stopBuzzer();
        _display.showSession(sessionTitle(), "Door closed");
        _network.logEvent("door_closed", "{\"box_id\":\"" + String(BOX_ID) + "\"}");
        if (_ctx.session != SessionMode::None) {
          _display.showReady();
          _ctx.session = SessionMode::None;
          _ctx.state = _network.isConnected() ? SmartBoxState::Idle : SmartBoxState::Offline;
        }
      }
    }

    if (_ctx.state == SmartBoxState::DoorOpen && doorOpen) {
      if (!_ctx.doorAlertSent && now - _ctx.doorOpenedAt > DOOR_OPEN_ALERT_MS) {
        startBuzzer();
        _ctx.doorAlertSent = true;
        _display.showError("Door open too long");
        _network.logEvent("door_timeout", "{\"box_id\":\"" + String(BOX_ID) + "\"}");
      }
    }

    switch (_ctx.state) {
    case SmartBoxState::Booting:
      handleBootState(now);
      break;
    case SmartBoxState::Offline:
      handleOfflineState(now);
      break;
    case SmartBoxState::Idle:
      handleIdleState(now);
      break;
    case SmartBoxState::AwaitingLookup:
      handleLookupState(now);
      break;
    case SmartBoxState::Unlocking:
      handleUnlockingState(now, doorOpen);
      break;
    case SmartBoxState::DoorOpen:
      handleDoorOpenState(now, doorOpen);
      break;
    }
  }

private:
  void handleBootState(uint32_t now) {
    if (_network.isConnected()) {
      _ctx.state = SmartBoxState::Idle;
      _display.showQrForUpload();
      _display.showReady();
      return;
    }
    if (now - _ctx.bootStarted > WIFI_BOOT_TIMEOUT_MS) {
      _ctx.state = SmartBoxState::Offline;
      _display.showOffline();
    }
  }

  void handleOfflineState(uint32_t now) {
    if (_network.isConnected()) {
      _ctx.state = SmartBoxState::Idle;
      _display.showReady();
      digitalWrite(PIN_STATUS_LED, HIGH);
      return;
    }
    if (now - _ctx.lastOfflineToast > 5000) {
      _display.showOffline();
      _ctx.lastOfflineToast = now;
    }
  }

  void handleIdleState(uint32_t now) {
    bool connected = _network.isConnected();
    digitalWrite(PIN_STATUS_LED, connected ? HIGH : LOW);
    if (_pcf.isPresent()) {
      _pcf.digitalWrite(1, connected ? HIGH : LOW);
    }
    String uid;
    if (_rfid.poll(now, uid)) {
      if (!_network.isConnected()) {
        _display.showOffline();
        _ctx.state = SmartBoxState::Offline;
        return;
      }
      _ctx.pendingUid = uid;
      _ctx.lookupAttempts = 0;
      _ctx.lookupNextAttempt = now;
      _display.showInfo("Authorising...");
      _ctx.state = SmartBoxState::AwaitingLookup;
    }
  }

  void handleLookupState(uint32_t now) {
    if (now < _ctx.lookupNextAttempt) {
      return;
    }
    if (_ctx.lookupAttempts >= 3) {
      _display.showError("Server unreachable");
      _ctx.state = SmartBoxState::Idle;
      return;
    }
    ++_ctx.lookupAttempts;
    BoxLookupResult res = _network.lookupTag(_ctx.pendingUid);
    if (!res.success) {
      _display.showError(res.message);
      _ctx.lookupNextAttempt = now + NETWORK_REQUEST_TIMEOUT_MS;
      return;
    }
    if (res.allowDeposit) {
      _ctx.session = SessionMode::Deposit;
    } else if (res.allowPickup) {
      _ctx.session = SessionMode::Pickup;
    } else {
      _ctx.session = SessionMode::None;
    }
    if (_ctx.session == SessionMode::None) {
      _display.showError("Access denied");
      _ctx.state = SmartBoxState::Idle;
      return;
    }
    unlockDoor(now);
  }

  void handleUnlockingState(uint32_t now, bool doorOpen) {
    if (doorOpen) {
      _ctx.state = SmartBoxState::DoorOpen;
      return;
    }
    if (now - _ctx.relayActivatedAt > 2000) {
      _display.showSession(sessionTitle(), "Pull door");
    }
  }

  void handleDoorOpenState(uint32_t now, bool doorOpen) {
    if (!doorOpen) {
      stopBuzzer();
      _display.showReady();
      _ctx.state = SmartBoxState::Idle;
    }
  }

  void unlockDoor(uint32_t now) {
    _ctx.state = SmartBoxState::Unlocking;
    activateRelay(now);
    _display.showSession(sessionTitle(), "Door unlocking");
    _network.logEvent("session_start", "{\"box_id\":\"" + String(BOX_ID) + "\",\"uid\":\"" +
                                            _ctx.pendingUid + "\"}");
  }

  void handleRelay(uint32_t now) {
    if (_ctx.relayActive && now - _ctx.relayActivatedAt >= RELAY_RELEASE_MS) {
      deactivateRelay();
    }
  }

  void activateRelay(uint32_t now) {
    digitalWrite(PIN_RELAY, RELAY_ACTIVE_LEVEL);
    _ctx.relayActive = true;
    _ctx.relayActivatedAt = now;
  }

  void deactivateRelay() {
    digitalWrite(PIN_RELAY, RELAY_ACTIVE_LEVEL == HIGH ? LOW : HIGH);
    _ctx.relayActive = false;
  }

  void startBuzzer() {
    if (_ctx.buzzerActive) {
      return;
    }
    digitalWrite(PIN_BUZZER, HIGH);
    _ctx.buzzerActive = true;
  }

  void stopBuzzer() {
    if (!_ctx.buzzerActive) {
      return;
    }
    digitalWrite(PIN_BUZZER, LOW);
    _ctx.buzzerActive = false;
  }

  void handleIr(uint32_t now) {
    static int lastState = -1;
    int current = digitalRead(PIN_IR_SENSOR);
    if (lastState == -1) {
      lastState = current;
      return;
    }
    if (current != lastState && current == HIGH) {
      if (now - _ctx.lastSnapshot >= IR_SNAPSHOT_INTERVAL_MS) {
        std::vector<uint8_t> jpeg;
        if (_camera.captureJpeg(jpeg)) {
          if (!_network.uploadSnapshot(jpeg)) {
            _display.showError("Snapshot upload failed");
          } else {
            _display.showInfo("Snapshot sent");
          }
          _ctx.lastSnapshot = now;
        }
      }
    }
    lastState = current;
  }

  String sessionTitle() const {
    switch (_ctx.session) {
    case SessionMode::Deposit:
      return "Deposit";
    case SessionMode::Pickup:
      return "Pickup";
    case SessionMode::None:
    default:
      return "Session";
    }
  }

  Display &_display;
  RfidReader &_rfid;
  CameraController &_camera;
  BoxNetworkClient &_network;
  Pcf8575Expander &_pcf;
  SmartBoxContext _ctx;
};
