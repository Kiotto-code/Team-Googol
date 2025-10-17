from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .db import engine, Base
from sqlalchemy import text
from .routers import audit_logs, users, items, boxes, cases
from .routers import admin_auth, admin_reports, system

# Create DB tables
Base.metadata.create_all(bind=engine)

# Lightweight migration for existing DBs: add users.role if missing
with engine.connect() as conn:
    # Check if 'role' column exists in 'users'
    result = conn.execute(text("PRAGMA table_info(users)"))
    columns = [row[1] for row in result.fetchall()]
    if "role" not in columns:
        # Add the column with default 'user' and NOT NULL
        conn.execute(text("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"))
    if "is_disabled" not in columns:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN is_disabled BOOLEAN NOT NULL DEFAULT 0"
            )
        )
    if "deleted_at" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN deleted_at DATETIME"))
    result = conn.execute(text("PRAGMA table_info(items)"))
    item_columns = [row[1] for row in result.fetchall()]
    if "updated_at" not in item_columns:
        conn.execute(text("ALTER TABLE items ADD COLUMN updated_at DATETIME"))
    if "deleted_at" not in item_columns:
        conn.execute(text("ALTER TABLE items ADD COLUMN deleted_at DATETIME"))
    result = conn.execute(text("PRAGMA table_info(cases)"))
    case_columns = [row[1] for row in result.fetchall()]
    if "remarks" not in case_columns:
        conn.execute(text("ALTER TABLE cases ADD COLUMN remarks TEXT"))
    if "deleted_at" not in case_columns:
        conn.execute(text("ALTER TABLE cases ADD COLUMN deleted_at DATETIME"))
    result = conn.execute(text("PRAGMA table_info(audit_logs)"))
    audit_columns = [row[1] for row in result.fetchall()]
    if audit_columns:
        if "entity_type" not in audit_columns:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_type TEXT"))
        if "entity_id" not in audit_columns:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_id TEXT"))
        if "metadata" not in audit_columns:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN metadata JSON"))
            conn.execute(text("UPDATE audit_logs SET metadata='{}' WHERE metadata IS NULL"))
    # Ensure check constraint exists (SQLite doesn't support adding named check constraints easily)
    # As a fallback, create a trigger to enforce allowed values on insert/update
    conn.execute(text("DROP TRIGGER IF EXISTS trg_users_role_insert"))
    conn.execute(text("DROP TRIGGER IF EXISTS trg_users_role_update"))
    conn.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS trg_users_role_insert
            BEFORE INSERT ON users
            FOR EACH ROW
            BEGIN
                SELECT CASE WHEN NEW.role NOT IN ('user','admin','staff') THEN
                    RAISE(ABORT, 'Invalid role value')
                END;
            END;
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS trg_users_role_update
            BEFORE UPDATE OF role ON users
            FOR EACH ROW
            BEGIN
                SELECT CASE WHEN NEW.role NOT IN ('user','admin','staff') THEN
                    RAISE(ABORT, 'Invalid role value')
                END;
            END;
            """
        )
    )

openapi_tags = [
    {"name": "admin-auth", "description": "Administrative authentication endpoints."},
    {"name": "admin-users", "description": "Administrative user management endpoints."},
    {"name": "users", "description": "Public user registration and login endpoints."},
    {"name": "admin-items", "description": "Administrative item management endpoints."},
    {"name": "items", "description": "Public item discovery endpoints."},
    {"name": "admin-boxes", "description": "Administrative storage box management."},
    {"name": "admin-cases", "description": "Administrative case tracking endpoints."},
    {"name": "admin-audit-logs", "description": "Administrative audit log access."},
    {"name": "system", "description": "Health and readiness probes."},
    {"name": "admin-metrics", "description": "Administrative monitoring metrics."},
    {"name": "admin-reports", "description": "Administrative reporting endpoints."},
]

app = FastAPI(
    title="Team-Googol Lost & Found API",
    version="0.1.0",
    description=(
        "Simple Lost & Found backend with SQLite. Use Swagger UI at /docs to try endpoints "
        "directly from the browser."
    ),
    openapi_tags=openapi_tags,
)

# Static and templates (resolve relative to this file)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
ADMIN_PANEL_DIR = BASE_DIR / "admin-panel"
if ADMIN_PANEL_DIR.exists():
    app.mount(
        "/admin-panel",
        StaticFiles(directory=str(ADMIN_PANEL_DIR), html=True),
        name="admin-panel",
    )
IMG_DIR = BASE_DIR.parent / "img"
if IMG_DIR.exists():
    app.mount(
        "/img",
        StaticFiles(directory=str(IMG_DIR)),
        name="img",
    )
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Include API routers
app.include_router(admin_auth.router)
app.include_router(users.admin_router)
app.include_router(users.public_router)
app.include_router(items.admin_router)
app.include_router(items.public_router)
app.include_router(boxes.router)
app.include_router(boxes.ws_router)
app.include_router(cases.router)
app.include_router(audit_logs.router)
app.include_router(system.router)
app.include_router(admin_reports.metrics_router)
app.include_router(admin_reports.reports_router)
