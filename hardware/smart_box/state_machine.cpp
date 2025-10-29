#include "state_machine.h"

#include <Arduino.h>

SmartBoxStateMachine::SmartBoxStateMachine(BoxNetworkClient &networkClient)
    : network_(networkClient) {}

void SmartBoxStateMachine::begin() {
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_DOOR_SENSOR, INPUT_PULLUP);
  pinMode(PIN_IR_SENSOR, INPUT_PULLUP);

  digitalWrite(PIN_RELAY, !RELAY_ACTIVE_LEVEL);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);

  lastDoorAlertMs_ = millis();
  lastSnapshotMs_ = millis();
}

void SmartBoxStateMachine::update() {
  const unsigned long now = millis();
  const bool doorOpen = digitalRead(PIN_DOOR_SENSOR) == HIGH;

  if (doorOpen) {
    digitalWrite(PIN_STATUS_LED, HIGH);
    if (!doorWasOpen_) {
      network_.logEvent("door_opened");
      doorWasOpen_ = true;
      lastDoorAlertMs_ = now;
    } else if (now - lastDoorAlertMs_ > DOOR_OPEN_ALERT_MS) {
      network_.logEvent("door_open_alert");
      lastDoorAlertMs_ = now;
    }
  } else if (doorWasOpen_) {
    network_.logEvent("door_closed");
    digitalWrite(PIN_STATUS_LED, LOW);
    doorWasOpen_ = false;
  }

  const bool parcelPresent = digitalRead(PIN_IR_SENSOR) == LOW;
  if (parcelPresent && now - lastSnapshotMs_ > IR_SNAPSHOT_INTERVAL_MS) {
    network_.logEvent("parcel_snapshot_requested");
    lastSnapshotMs_ = now;
  }
}
