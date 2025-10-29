# Smart Box Firmware

This directory contains the Arduino sketch and supporting modules for the Route-A smart locker controller. The project targets ESP8266-based development boards with a TFT display, MFRC522 RFID reader, camera module, PCF8575 I/O expander, and buzzer/relay accessories.

## Building with the Arduino IDE

1. Install the **ESP8266** board package via *File → Preferences → Additional Boards Manager URLs* adding `https://arduino.esp8266.com/stable/package_esp8266com_index.json`, then use *Tools → Board → Boards Manager* to install "esp8266".
2. Install required libraries from the Library Manager:
   - **Adafruit ST7735 and ST7789 Library** (installs Adafruit GFX automatically)
   - **MFRC522** RFID library
   - **qrcode** (optional; enables true QR rendering on the TFT)
3. Open `firmware/smart_box/smart_box.ino` in the Arduino IDE. The IDE will automatically load the accompanying `.cpp` and `.h` files.
4. Select your ESP8266 board (e.g., *NodeMCU 1.0 (ESP-12E Module)*) and correct COM/serial port.
5. Click **Verify** to build. Resolve any missing library warnings if they appear.
6. Use **Upload** to flash the firmware. On first boot, monitor the Serial console at 115200 baud to observe state transitions and diagnostics.

