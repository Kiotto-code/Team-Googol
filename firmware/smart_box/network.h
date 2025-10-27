#pragma once

#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <vector>

#include "config.h"

struct LookupResult {
  bool success;
  bool allowDeposit;
  bool allowPickup;
  String message;
};

class NetworkClient {
public:
  NetworkClient() : _lastAttempt(0), _connected(false) {}

  void begin() {
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    _lastAttempt = millis();
  }

  void loop(uint32_t now) {
    if (WiFi.status() == WL_CONNECTED) {
      _connected = true;
      return;
    }
    _connected = false;
    if (now - _lastAttempt > 5000) {
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      _lastAttempt = now;
    }
  }

  bool isConnected() const { return WiFi.status() == WL_CONNECTED; }

  bool waitForConnectivity(uint32_t timeoutMs) {
    uint32_t start = millis();
    while (millis() - start < timeoutMs) {
      if (WiFi.status() == WL_CONNECTED) {
        return true;
      }
      delay(100);
    }
    return false;
  }

  bool logEvent(const String &type, const String &payload) {
    if (!isConnected()) {
      return false;
    }
    HTTPClient client;
    String url = String(SERVER_BASE_URL) + ENDPOINT_EVENT_LOG;
    if (!client.begin(url)) {
      return false;
    }
    client.setTimeout(NETWORK_REQUEST_TIMEOUT_MS);
    client.addHeader("Content-Type", "application/json");
    String body = String("{\"box_id\":\"") + BOX_ID + "\",\"type\":\"" + type + "\",\"payload\":" + payload + "}";
    int code = client.POST(body);
    client.end();
    return code > 0 && code < 400;
  }

  LookupResult lookupTag(const String &uid) {
    LookupResult result{false, false, false, ""};
    if (!isConnected()) {
      result.message = "Offline";
      return result;
    }
    HTTPClient client;
    String url = String(SERVER_BASE_URL) + ENDPOINT_RFID_LOOKUP + "?box_id=" + BOX_ID + "&uid=" + uid;
    if (!client.begin(url)) {
      result.message = "Init fail";
      return result;
    }
    client.setTimeout(NETWORK_REQUEST_TIMEOUT_MS);
    int code = client.GET();
    if (code == 200) {
      String payload = client.getString();
      payload.toLowerCase();
      result.success = true;
      result.allowDeposit = payload.indexOf("deposit") >= 0;
      result.allowPickup = payload.indexOf("pickup") >= 0;
      result.message = payload;
    } else {
      result.message = String("HTTP") + code;
    }
    client.end();
    return result;
  }

  bool uploadSnapshot(const std::vector<uint8_t> &jpeg) {
    if (!isConnected()) {
      return false;
    }
    HTTPClient client;
    String url = String(SERVER_BASE_URL) + ENDPOINT_UPLOAD;
    if (!client.begin(url)) {
      return false;
    }
    client.setTimeout(NETWORK_REQUEST_TIMEOUT_MS);
    client.addHeader("Content-Type", "application/octet-stream");
    int code = client.POST(jpeg.data(), jpeg.size());
    client.end();
    return code > 0 && code < 400;
  }

private:
  uint32_t _lastAttempt;
  bool _connected;
};
