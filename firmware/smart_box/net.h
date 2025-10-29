#pragma once

#include <Arduino.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>

#include <functional>
#include <vector>

#include "config.h"

class SmartBoxNetwork {
 public:
  void begin();
  bool ensureWifi(uint32_t timeoutMs = SmartBoxConfig::kWifiConnectTimeoutMs);

  bool postEvent(const String &path, const String &payload);
  bool uploadSnapshot(const String &metadataJson, std::function<bool(HTTPClient &)> uploader);

 private:
  bool httpPost(const String &url, const String &payload, HTTPClient &client);
};

