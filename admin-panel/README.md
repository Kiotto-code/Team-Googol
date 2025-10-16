# Admin Panel

This Vite + React 19 + TypeScript project implements the administrative console described in the information architecture.

## Getting started

```bash
npm install
npm run dev
```

Copy `.env.example` to `.env` if you need to customise API hosts, WebSocket URLs, or the default timezone. The app is mounted
under the `/admin-panel` base path. The development server is available at `http://localhost:5173/admin-panel` when started
locally.

### Testing & linting

```bash
npm run lint
npm test
npm run test:watch
```

Vitest is configured with React Testing Library to exercise authentication flows, table interactions, and WebSocket reconnect
logic.

### Build

```bash
npm run build
```

The build output lives in `dist/` and can be hosted from any CDN or reverse proxy. Because the Vite `base` is set to
`/admin-panel`, every asset is generated under that prefix.

### Deployment notes

If the frontend is co-hosted with a FastAPI backend you can serve the static bundle with:

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

For Nginx, proxy the `/admin-panel/` prefix to the built assets:

```
location /admin-panel/ {
    alias /var/www/admin-panel/dist/;
    try_files $uri $uri/ /admin-panel/index.html;
}
```

## Tech stack

- React 19 with TypeScript and React Router for nested routing
- Tailwind CSS with shadcn/ui components for styling and layout
- Zustand for auth and UI state (theme, language, timezone)
- Axios with access token/refresh interceptors for `/api/v1/admin`
- React Query for data fetching and caching
- React Hook Form + Zod for schema driven forms
- Recharts, TanStack Table, and Sonner toasts for analytics and data grids
- I18next for EN/ZH translations and localized timestamps (Asia/Kuala Lumpur by default with UTC toggle)
- WebSocket client with heartbeat and reconnect logic for `/api/v1/admin/ws/boxes`
