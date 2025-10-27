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
