# Smart Box Test Plan

This plan verifies the end-to-end behaviour of the smart box firmware with emphasis on door control, deposit and pickup flows, timeout safety, and offline resiliency.

## 1. Deposit Flow
1. Power the unit and wait for the **AVAILABLE** screen (QR code or text URL).
2. Press the physical door button (wired to PCF8575 P03).
3. Confirm the relay energises for ~5 seconds and the display shows "Door unlocked".
4. Open the door, place a parcel, and close the door.
5. Observe that the state transitions to **Verifying deposit**, the camera captures an image, and `/api/box/deposit` is posted (monitor backend logs).
6. Verify the screen returns to **AVAILABLE** and the buzzer is silent.

## 2. Pickup Flow
1. Present a valid RFID tag (registered in the backend) within range of the MFRC522 reader.
2. Confirm the Serial console logs the UID and the relay energises to unlock the door.
3. Remove the parcel and close the door.
4. Validate that the firmware performs a pickup snapshot and posts `/api/box/pickup` metadata.
5. Ensure the screen returns to **AVAILABLE**.

## 3. Door Timeout Safety
1. Trigger a door unlock (button or RFID) but keep the door open.
2. After 30 seconds verify that the buzzer plays the timeout pattern, the screen shows an error, and Serial logs the transition to **ERROR**.
3. Close the door and confirm the firmware automatically returns to **AVAILABLE** with the buzzer silenced.

## 4. Offline Retry Behaviour
1. Disconnect Wi-Fi or power down the access point before booting the device.
2. Power cycle the smart box. Confirm it attempts to connect for 15 seconds during **BOOT**.
3. After timeout, verify the screen shows an error and Serial logs **ERROR** state.
4. Restore Wi-Fi and close the door (if open). Ensure the device reconnects (using `ensureWifi`) and transitions back to **AVAILABLE** on the next loop iteration.
5. During deposit or pickup verification, temporarily disrupt Wi-Fi and confirm the firmware retries HTTP uploads up to three times before reporting failure (monitor Serial output).

## 5. IR Snapshot Rate Limiting
1. With the door closed and the box in **AVAILABLE**, wave a hand across the IR beam (PCF8575 P00).
2. Confirm the firmware captures a snapshot and posts a deposit event (Serial log shows camera bytes).
3. Repeat the IR trigger within 20 seconds and ensure a second snapshot is **not** captured (no additional camera log).
4. Wait longer than 20 seconds, trigger again, and confirm a new snapshot occurs.

