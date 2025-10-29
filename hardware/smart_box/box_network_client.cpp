#include "box_network_client.h"

#include <Arduino.h>

BoxNetworkClient::BoxNetworkClient() = default;

bool BoxNetworkClient::ensureConnected() const {
  return WiFi.status() == WL_CONNECTED;
}

bool BoxNetworkClient::performPost(const String &url, const String &body, const char *contentType) const {
  if (!ensureConnected()) {
    return false;
  }

  HTTPClient http;
  if (!http.begin(url)) {
    return false;
  }
  http.addHeader("Content-Type", contentType);
  http.setTimeout(NETWORK_REQUEST_TIMEOUT_MS);

  const int status = http.POST(body);
  http.end();
  return status > 0 && status < 400;
}

bool BoxNetworkClient::logEvent(const String &eventType, const String &details) {
  const String url = String(SERVER_BASE_URL) + ENDPOINT_EVENT_LOG;
  const String payload = String("{\"boxId\":\"") + BOX_ID + "\",\"event\":\"" + eventType +
                         "\",\"details\":\"" + details + "\"}";
  return performPost(url, payload, "application/json");
}

LookupResult BoxNetworkClient::lookupRfid(const String &tagId) {
  LookupResult result{};
  if (!ensureConnected()) {
    return result;
  }
  const String url = String(SERVER_BASE_URL) + ENDPOINT_RFID_LOOKUP + "?tag=" + tagId;
  HTTPClient http;
  if (!http.begin(url)) {
    return result;
  }
  http.setTimeout(NETWORK_REQUEST_TIMEOUT_MS);

  const int status = http.GET();
  if (status > 0 && status < 400) {
    result.success = true;
    result.userName = http.getString();
  }
  http.end();
  return result;
}

bool BoxNetworkClient::uploadSnapshot(const std::vector<uint8_t> &jpegData) {
  if (!ensureConnected() || jpegData.empty()) {
    return false;
  }

  const String url = String(SERVER_BASE_URL) + ENDPOINT_UPLOAD;
  HTTPClient http;
  if (!http.begin(url)) {
    return false;
  }
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(NETWORK_REQUEST_TIMEOUT_MS);

  std::vector<uint8_t> buffer(jpegData.begin(), jpegData.end());
  const int status = http.POST(buffer.data(), buffer.size());
  http.end();
  return status > 0 && status < 400;
}
