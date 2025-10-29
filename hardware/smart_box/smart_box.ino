#include <SPI.h>
#include <WiFi.h>

#include "box_network_client.h"
#include "config.h"
#include "state_machine.h"

SPIClass sharedSPI(FSPI);
BoxNetworkClient networkClient;
SmartBoxStateMachine stateMachine(networkClient);

namespace {
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_BOOT_TIMEOUT_MS) {
    delay(250);
  }
}
}  // namespace

void setup() {
  Serial.begin(115200);
  sharedSPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);

  connectWiFi();
  stateMachine.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  stateMachine.update();
  delay(50);
}
