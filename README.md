# Team-Googol FastAPI app

Simple FastAPI backend + Jinja2 frontend served from the same server, using SQLite. A Vite-powered admin panel lives in the
`admin-panel/` directory and is mounted under `/admin-panel` in production.

## Backend (Python 3.10.12)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000 for the default UI and API explorer.

### API

- Users: `GET/POST /users`
- Items: `GET/POST /items`
- Boxes: `GET/POST /boxes`
- Cases: `GET/POST /cases`

Example create payloads:

- `POST /users`
  ```json
  {
    "name": "Alice",
    "email": "alice@example.com",
    "password": "secret",
    "rfid_tag": "RF123"
  }
  ```
- `POST /items`
  ```json
  { "description": "Black wallet", "status": "available" }
  ```
- `POST /boxes`
  ```json
  { "location": "Lobby", "status": true }
  ```
- `POST /cases`
  ```json
  { "box_id": 1, "item_id": 1, "status": "available" }
  ```

The SQLite DB is created automatically at startup with tables matching the design (auto-increment PKs, FKs, uniques,
timestamps with default `now()`).

## Admin Panel (Vite + React)

The React admin interface lives under `admin-panel/` and is built with Vite, React 19, TanStack Table, Zustand, and Tailwind.
It is designed to be published under the `/admin-panel` sub-path of the FastAPI app.

### Prerequisites

- Node.js 20+
- npm 10+

### Initial setup

```bash
cd admin-panel
cp .env.example .env     # adjust values as needed
npm install
```

Environment variables live in `.env` (Vite style). The included `.env.example` documents the available flags:

- `VITE_API_BASE_URL` – REST base URL (usually `http://localhost:8000/api/v1/admin` in development).
- `VITE_WS_URL` – WebSocket endpoint for live box events (the auth token is appended automatically).
- `VITE_DEFAULT_TZ` – Default timezone for date formatting (`Asia/Kuala_Lumpur` or `UTC`).
- `VITE_AUTH_STORAGE` – Storage location for auth/session data (`local` for `localStorage`, `session` for `sessionStorage`).

### Local development

```bash
npm run dev
```

Vite serves the SPA at `http://localhost:5173/admin-panel`. API calls are proxied to the URL configured via `VITE_API_BASE_URL`.

### Quality checks

```bash
npm run lint       # ESLint type-aware lint rules
npm test           # Vitest unit/integration suite (non-watch)
npm run test:watch # Vitest in watch mode for local development
```

Vitest is configured with React Testing Library. The suite covers login success/failure flows, table pagination/filter
behaviour, and WebSocket reconnect handling.

### Build

```bash
npm run build
```

The production bundle is emitted to `admin-panel/dist/` with asset paths rooted at `/admin-panel`. Static assets can be hosted
by any CDN or reverse proxy.

### Deploying alongside FastAPI

Mount the compiled assets directly in `app.main` so FastAPI serves the SPA under `/admin-panel`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount(
    "/admin-panel",
    StaticFiles(directory="admin-panel/dist", html=True),
    name="admin_panel",
)
```

Ensure the FastAPI backend exposes the admin APIs under `/api/v1/admin` and the WebSocket endpoint under
`/api/v1/admin/ws/boxes` to match the defaults in `.env.example`.

### Nginx SPA configuration

Serve the built SPA with a fallback to `index.html` so client-side routing works:

```
location /admin-panel/ {
    alias /var/www/admin-panel/dist/;
    try_files $uri $uri/ /admin-panel/index.html;
}
```

Proxy `/api/v1/admin/` and `/api/v1/admin/ws/` to the FastAPI application (e.g. via `proxy_pass http://127.0.0.1:8000;`) so
the SPA and backend share the same domain and cookies.
