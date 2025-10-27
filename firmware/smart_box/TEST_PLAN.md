# Smart Box Firmware Test Plan

## Scope
Functional smoke validation for the ESP32-S3 smart box firmware covering deposit, pickup, door timeout safety, and offline resilience.

## Preconditions
- Device flashed with `SmartBox.ino` build.
- Box connected to HONOR Wi-Fi (or test AP with same credentials).
- Backend staging server reachable via URLs configured in `config.h`.
- Parcel door closed, RFID cards enrolled for both deposit and pickup scenarios.

## Test Cases

### 1. Deposit Happy Path
1. Power on device; verify TFT shows "Ready" and QR upload screen once Wi-Fi connects.
2. Present courier RFID card.
3. Confirm display shows "Deposit" session and relay unlocks door within 2 s.
4. Open door; ensure event logged on server dashboard.
5. Place parcel so that IR trip sensor toggles; confirm buzzer stays silent and snapshot upload succeeds (status toast on TFT).
6. Close door; verify relay releases, display returns to Ready, and session end logged.

### 2. Pickup Happy Path
1. Present recipient RFID card while device is idle.
2. Confirm "Pickup" prompt and door unlock.
3. Open and close door without tripping IR sensor; ensure no snapshot attempt occurs.
4. Verify pickup completion event recorded by server.

### 3. Door-Open Timeout Alert
1. Start deposit or pickup session and leave door open for longer than 30 s.
2. Observe buzzer activates and TFT shows timeout error message.
3. Confirm server receives `door_timeout` log entry.
4. Close door; ensure buzzer stops and device returns to Ready state.

### 4. Offline Retry Behaviour
1. Block Wi-Fi access (disable AP) and reboot device.
2. After 15 s, confirm display shows "Offline" status.
3. Present RFID card; verify access is denied with error message and no unlock occurs.
4. Restore Wi-Fi; observe device auto-reconnects, display returns to Ready, and RFID access works without reflashing.

## Exit Criteria
- All four scenarios executed successfully.
- Any deviations recorded with firmware version and environment notes.
