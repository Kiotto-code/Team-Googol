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

- Users: GET/POST /users
- Items: GET/POST /items
- Boxes: GET/POST /boxes
- Cases: GET/POST /cases

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
