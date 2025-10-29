#pragma once

#include <Arduino.h>

#include <functional>

class SmartBoxCamera {
 public:
  void begin();
  bool captureJpeg(std::function<void(const uint8_t *data, size_t len)> onChunk);
};

