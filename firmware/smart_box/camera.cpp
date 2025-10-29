#include "camera.h"

void SmartBoxCamera::begin() {
  Serial.println(F("[CAMERA] init"));
}

bool SmartBoxCamera::captureJpeg(
    std::function<void(const uint8_t *data, size_t len)> onChunk) {
  static const uint8_t fakeData[] = {0xFF, 0xD8, 0xFF, 0xD9};
  if (onChunk) {
    onChunk(fakeData, sizeof(fakeData));
  }
  Serial.println(F("[CAMERA] capture stub"));
  return true;
}

