#pragma once

#include <Arduino.h>

class SmartBoxDisplay {
 public:
  void begin();
  void showBoot();
  void showAvailable(const String &boxId);
  void showStatus(const String &message);
  void showError(const String &error);

 private:
  void drawQr(const String &text);
};

