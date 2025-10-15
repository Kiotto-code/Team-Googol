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

## API

Admin routes (`/api/v1/admin`):

- Users: GET/POST `/api/v1/admin/users`
- Items: POST `/api/v1/admin/items`
- Items upload: POST `/api/v1/admin/items/upload`
- Boxes: GET/POST `/api/v1/admin/boxes`
- Cases: GET/POST `/api/v1/admin/cases`

Public routes (`/api/v1`):

- Users: POST `/api/v1/users/register`, POST `/api/v1/users/login`
- Items: GET `/api/v1/items`

Example create payloads:

- POST /api/v1/admin/users
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "secret",
  "rfid_tag": "RF123"
}
```

- POST /api/v1/admin/items
```json
{ "description": "Black wallet", "status": "available" }
```

- POST /api/v1/admin/boxes
```json
{ "location": "Lobby", "status": true }
```

- POST /api/v1/admin/cases
```json
{ "box_id": 1, "item_id": 1, "status": "available" }
```

## DB Schema

The SQLite DB is created automatically at startup with tables: users, items, boxes, cases, matching the provided design (auto-increment PKs, FKs, uniques, timestamps with default now()).
