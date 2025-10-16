# Admin Panel Frontend

This directory contains the standalone administrative control center that is served from `/admin-panel` by the FastAPI application. The UI is a vanilla JavaScript single-page application that uses hash-based routing so that deep links work even when the static files are served directly by FastAPI.

## Structure

```
app/admin-panel/
├── index.html
├── styles.css
├── main.js
├── api.js
├── router.js
├── components/
│   ├── app-card.js
│   ├── app-modal.js
│   ├── app-table.js
│   ├── app-toast.js
│   └── code-block.js
├── pages/
│   ├── audit-logs.js
│   ├── boxes.js
│   ├── cases.js
│   ├── dashboard.js
│   ├── items.js
│   ├── metrics.js
│   ├── profile.js
│   ├── reports.js
│   ├── users.js
│   └── index.js
├── assets/
│   └── logo.svg
└── README.md
```

## Serving the panel

The FastAPI application automatically mounts this directory at `/admin-panel`. No additional configuration is required while running the default Uvicorn server:

```bash
uvicorn app.main:app --reload
```

After the backend starts, open [http://localhost:8000/admin-panel](http://localhost:8000/admin-panel) to access the UI. The panel only renders once you authenticate against the administrative API.

## Configuring the API endpoint

By default the frontend sends requests to `/api/v1`. If you proxy the backend behind a different prefix (for example when running behind an ingress controller) you can override the API base URL by defining `window.API_BASE` before loading `main.js`:

```html
<script>
  window.API_BASE = 'https://internal.example.com/api/v1';
</script>
<script type="module" src="./main.js"></script>
```

`API_BASE` should always point to the root of the FastAPI REST namespace (the path that prefixes `/admin/...` routes). Tokens are stored in `sessionStorage`, so a refresh keeps the session alive within the same browser tab but closes automatically when the tab is closed.

## Development tips

* The router uses URL hashes (`#/dashboard`, `#/boxes`, …), so you can refresh the browser without hitting a server-side route.
* WebSocket telemetry for the boxes view requires the administrative access token. If the token expires the client automatically requests a new one using the refresh token and reconnects.
* The styles implement a 12-column responsive grid, a dark enterprise theme, accessible focus states, and keyboard interaction for table rows and modals.
