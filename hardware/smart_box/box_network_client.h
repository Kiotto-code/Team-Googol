#pragma once

#include <HTTPClient.h>
#include <WiFi.h>
#include <vector>

#include "config.h"

struct LookupResult {
  bool success = false;
  String userName;
};

// Lightweight wrapper around the Arduino HTTPClient that avoids the name clash with
// ESP-IDF's NetworkClient definition on Windows systems.
class BoxNetworkClient {
 public:
  BoxNetworkClient();

  bool logEvent(const String &eventType, const String &details = "");
  LookupResult lookupRfid(const String &tagId);
  bool uploadSnapshot(const std::vector<uint8_t> &jpegData);

 private:
  bool ensureConnected() const;
  bool performPost(const String &url, const String &body, const char *contentType) const;
};
