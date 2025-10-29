#include <Arduino.h>

#include "buzzer.h"
#include "camera.h"
#include "config.h"
#include "display.h"
#include "net.h"
#include "pcf8575.h"
#include "rfid.h"
#include "state_machine.h"

SmartBoxNetwork network;
SmartBoxDisplay display;
PcF8575Driver expander;
SmartBoxRfid rfid(SmartBoxConfig::kSpiCsRfidPin, D3);
SmartBoxCamera camera;
SmartBoxBuzzer buzzer(D8);
SmartBoxStateMachine stateMachine;

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println(F("Smart box boot"));

  network.begin();
  display.begin();
  camera.begin();
  buzzer.begin();
  rfid.begin();
  expander.begin();

  SmartBoxContext ctx{&network, &display, &expander, &rfid, &camera, &buzzer};
  stateMachine.begin(ctx);
}

void loop() {
  rfid.loop();
  stateMachine.loop();
  delay(10);
}

