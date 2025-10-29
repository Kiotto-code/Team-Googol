#include "net.h"

void SmartBoxNetwork::begin() {
  WiFi.mode(WIFI_STA);
}

bool SmartBoxNetwork::ensureWifi(uint32_t timeoutMs) {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  Serial.println(F("[NET] Connecting to Wi-Fi"));
  WiFi.begin(SmartBoxConfig::kWifiSsid, SmartBoxConfig::kWifiPassword);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < timeoutMs) {
    delay(250);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print(F("[NET] Connected IP: "));
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println(F("[NET] Wi-Fi connect timeout"));
  return false;
}

bool SmartBoxNetwork::httpPost(const String &url, const String &payload, HTTPClient &client) {
  WiFiClient wifiClient;
  if (!client.begin(wifiClient, url)) {
    Serial.println(F("[NET] Failed to begin HTTP client"));
    return false;
  }
  client.setTimeout(SmartBoxConfig::kHttpRequestTimeoutMs);
  client.addHeader("Content-Type", "application/json");

  int code = client.POST(payload);
  if (code >= 200 && code < 300) {
    Serial.print(F("[NET] POST success: "));
    Serial.println(code);
    client.end();
    return true;
  }

  Serial.print(F("[NET] POST failed: "));
  Serial.println(code);
  client.end();
  return false;
}

bool SmartBoxNetwork::postEvent(const String &path, const String &payload) {
  String url = String(F("https://locker-backend.local")) + path;
  HTTPClient client;
  for (uint8_t attempt = 0; attempt < 3; ++attempt) {
    if (httpPost(url, payload, client)) {
      return true;
    }
    delay(200);
  }
  return false;
}

bool SmartBoxNetwork::uploadSnapshot(const String &metadataJson,
                                     std::function<bool(HTTPClient &)> uploader) {
  String url = String(F("https://locker-backend.local/upload"));
  for (uint8_t attempt = 0; attempt < 3; ++attempt) {
    HTTPClient client;
    WiFiClient wifiClient;
    if (!client.begin(wifiClient, url)) {
      delay(200);
      continue;
    }
    client.setTimeout(SmartBoxConfig::kHttpRequestTimeoutMs);
    bool uploaded = uploader(client);
    client.end();
    if (!uploaded) {
      delay(200);
      continue;
    }
    HTTPClient metadataClient;
    if (httpPost(String(F("https://locker-backend.local/upload/metadata")), metadataJson, metadataClient)) {
      return true;
    }
  }
  return false;
}

