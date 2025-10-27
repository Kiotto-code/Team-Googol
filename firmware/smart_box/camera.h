#pragma once

#include <Arduino.h>
#include <esp_camera.h>
#include <vector>

class CameraController {
public:
  CameraController() : _initialised(false) {}

  bool begin() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = 8;
    config.pin_d1 = 9;
    config.pin_d2 = 10;
    config.pin_d3 = 11;
    config.pin_d4 = 12;
    config.pin_d5 = 13;
    config.pin_d6 = 14;
    config.pin_d7 = 15;
    config.pin_xclk = 40;
    config.pin_pclk = 39;
    config.pin_vsync = 38;
    config.pin_href = 37;
    config.pin_sccb_sda = 35;
    config.pin_sccb_scl = 36;
    config.pin_pwdn = -1;
    config.pin_reset = -1;
    config.xclk_freq_hz = 20000000;
    config.frame_size = FRAMESIZE_SVGA;
    config.pixel_format = PIXFORMAT_JPEG;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.jpeg_quality = 12;
    config.fb_count = 2;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
      Serial.printf("Camera init failed: %d\n", err);
      _initialised = false;
      return false;
    }
    _initialised = true;
    sensor_t *sensor = esp_camera_sensor_get();
    if (sensor) {
      sensor->set_framesize(sensor, FRAMESIZE_SVGA);
    }
    return true;
  }

  bool captureJpeg(std::vector<uint8_t> &buffer) {
    if (!_initialised) {
      if (!begin()) {
        return false;
      }
    }
    const uint8_t maxAttempts = 3;
    for (uint8_t attempt = 0; attempt < maxAttempts; ++attempt) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) {
        delay(50);
        continue;
      }
      if (fb->format != PIXFORMAT_JPEG) {
        esp_camera_fb_return(fb);
        delay(50);
        continue;
      }
      buffer.assign(fb->buf, fb->buf + fb->len);
      esp_camera_fb_return(fb);
      return true;
    }
    Serial.println("Camera capture failed after retries");
    _initialised = false;
    return false;
  }

private:
  bool _initialised;
};
