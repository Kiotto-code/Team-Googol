#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>

#include "camera.h"
#include "config.h"
#include "display.h"
#include "network.h"
#include "pcf8575.h"
#include "rfid.h"
#include "state_machine.h"

SPIClass sharedSPI(FSPI);
Display display;
RfidReader rfid;
CameraController cameraController;
NetworkClient networkClient;
Pcf8575Expander pcf8575;
SmartBoxStateMachine stateMachine(display, rfid, cameraController, networkClient, pcf8575);

void setup() {
  Serial.begin(115200);
  delay(200);
  pinMode(PIN_TFT_CS, OUTPUT);
  digitalWrite(PIN_TFT_CS, HIGH);
  pinMode(PIN_RFID_SS, OUTPUT);
  digitalWrite(PIN_RFID_SS, HIGH);

  Wire1.begin(PIN_I2C1_SDA, PIN_I2C1_SCL, 100000);
  if (pcf8575.begin(Wire1)) {
    Serial.print("PCF8575 detected at 0x");
    Serial.println(pcf8575.address(), HEX);
  } else {
    Serial.println("PCF8575 not detected");
  }

  sharedSPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI, PIN_RFID_SS);
  display.begin(sharedSPI);
  rfid.begin(sharedSPI);

  stateMachine.begin();
  Serial.println("Smart box ready");
}

void loop() {
  stateMachine.update(millis());
}
