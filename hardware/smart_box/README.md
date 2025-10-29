# Smart Box firmware

This folder contains an ESP32 sketch that accompanies the hardware prototype
for Team Googol's smart delivery box.  The original prototype used several
headers whose names only differed in letter casing (for example `Network.h`
and `network.h`).  That layout works on Linux and macOS, but fails to build on
Windows because the filesystem is case-insensitive.  The sketch here avoids
those clashes by:

- Consolidating all network operations behind `box_network_client.h`, which is
  named uniquely and no longer shadows the ESP-IDF `NetworkClient` type.
- Using a single entry-point sketch `smart_box.ino` so the build system never
  sees multiple `*.ino` files that only differ in casing.

The code only relies on standard Arduino libraries (`WiFi`, `HTTPClient`, and
`SPI`) and should build with the stock ESP32 board support package.
