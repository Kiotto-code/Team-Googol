# Team-Googol FastAPI app

Simple FastAPI backend + Jinja2 frontend served from the same server, using SQLite.

## Run locally (Python 3.10.12)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000 for a minimal UI.

## Web URLs (local)

- Home page: http://127.0.0.1:8000/
- Admin Panel (SPA): http://127.0.0.1:8000/admin-panel/
- Finder/Upload page: http://127.0.0.1:8000/upload (redirects to /upload-page/)
- Swagger API docs: http://127.0.0.1:8000/docs
- ReDoc docs: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/api/v1/healthz
- Readiness check: http://127.0.0.1:8000/api/v1/readyz
- Public image uploads: http://127.0.0.1:8000/uploads/
- Static assets: http://127.0.0.1:8000/static/

Public APIs commonly used by web UI:
- Items (public): /api/v1/items/...
- Boxes (public): /api/v1/boxes/{box_id}
- Users (public): /api/v1/users/register, /api/v1/users/login

Admin APIs (require admin/staff role):
- Users: /api/v1/admin/users
- Items: /api/v1/admin/items
- Boxes: /api/v1/admin/boxes
- Cases: /api/v1/admin/cases
- Audit Logs: /api/v1/admin/audit-logs
- Metrics & Reports: /api/v1/admin/metrics, /api/v1/admin/reports

## API

- Users: GET/POST /users
- Items: GET/POST /items
- Boxes: GET/POST /boxes
- Cases: GET/POST /cases

### Smart box firmware API

ESP32 smart boxes interact with the backend through `/api/v1/boxes` endpoints. Each handler
returns a `DeviceBoxActionResponse` payload:

```json
{
  "box_id": 1,
  "action": "deposit_unlock",
  "box_status": true,
  "door_status": true,
  "telemetry_id": 42,
  "user_id": null,
  "metadata": {"request_id": "req-123"}
}
```

Endpoints and request bodies:

| Endpoint | Purpose | Request body |
| --- | --- | --- |
| `POST /api/v1/boxes/{box_id}/deposit/unlock` | Unlock door for a deposit when the box is available. | `{"request_id": "req-123", "device_id": "ESP32-01"}` |
| `POST /api/v1/boxes/{box_id}/deposit/complete` | Mark the deposit complete, close the door, and flip the box to FULL. | `{"request_id": "req-124", "load": 1, "door_closed": true}` |
| `POST /api/v1/boxes/{box_id}/pickup/validate` | Validate a pickup via RFID and unlock the door. | `{"request_id": "req-200", "rfid_uid": "RF123"}` |
| `POST /api/v1/boxes/{box_id}/pickup/complete` | Mark a pickup as completed and return the box to AVAILABLE (optional photo metadata allowed). | `{"request_id": "req-201", "rfid_uid": "RF123", "photo_url": "https://..."}` |
| `POST /api/v1/boxes/{box_id}/door-timeout` | Log a door-open timeout with duration information. | `{"request_id": "req-300", "duration_seconds": 120, "door_open": true}` |
| `POST /api/v1/boxes/{box_id}/activity` | Record IR sensor activity while the door is closed. | `{"request_id": "req-400", "triggered": true, "sensor_value": 512}` |

All device endpoints enforce the following invariants:

- A box must be AVAILABLE (`box.status == true`) to start a deposit flow.
- A box must be FULL (`box.status == false`) to start a pickup flow.
- Door state transitions (`door_status`) always mirror the hardware request and are recorded in box telemetry and audit logs.

Example create payloads:

- POST /users
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "secret",
  "rfid_tag": "RF123"
}
```

- POST /items
```json
{ "description": "Black wallet", "status": "available" }
```

- POST /boxes
```json
{ "location": "Lobby", "status": true }
```

- POST /cases
```json
{ "box_id": 1, "item_id": 1, "status": "available" }
```

## DB Schema

The SQLite DB is created automatically at startup with tables: users, items, boxes, cases, matching the provided design (auto-increment PKs, FKs, uniques, timestamps with default now()).

## Smart Box Firmware (ESP32-S3-CAM)

An Arduino sketch for the ESP32-S3 smart locker lives in `firmware/smart_box/`. The firmware drives the TFT, RFID, PCF8575 I/O expander, MFRC522 reader, and on-board camera using non-blocking timers and the shared SPI bus.

### Building with Arduino IDE

1. Install the ESP32 board package v2.0.11 or newer from Espressif.
2. Open `firmware/smart_box/SmartBox.ino` in Arduino IDE.
3. From **Tools → Board**, pick **ESP32S3 Dev Module**.
4. Enable PSRAM (Tools → PSRAM → Enabled) and choose QSPI mode if available. Leave Flash at 80 MHz and `Huge APP` partition for camera buffers.
5. Install required libraries if prompted: `Adafruit ST7735 and ST7789 Library`, `Adafruit GFX Library`, `MFRC522`, and `QRCode`.
6. Connect the ESP32-S3-CAM board via USB, select the correct port, then click **Upload**.

On boot, the display shows Wi-Fi status and a QR code for `/upload-page?box_id=SMART_BOX_001`. Further validation steps are listed in `firmware/smart_box/TEST_PLAN.md`.
