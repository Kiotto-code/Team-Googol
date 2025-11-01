from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .db import engine, Base
from sqlalchemy import text
from .routers import audit_logs, users, items, boxes, cases
from .routers import admin_auth, admin_reports, system
from .routers import activity as activity_router
from .routers import device_boxes

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
    {"name": "device-boxes", "description": "Firmware-facing smart box integration APIs."},
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

from fastapi.middleware.cors import CORSMiddleware

# Allow your frontend origins
origins = [
    "http://127.0.0.1:5501",
    "http://localhost:5501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers=["*"],
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

# HOME PAGE
HOME_PAGE_DIR = BASE_DIR / "home-page"

if HOME_PAGE_DIR.exists():
    app.mount(
        "/home-page",
        StaticFiles(directory=str(HOME_PAGE_DIR), html=True),
        name="home-page",
    )

@app.get("/home")
def redirect_to_index():
    return RedirectResponse(url="/home-page/")

# COLLECT PAGE
COLLECT_PAGE_DIR = BASE_DIR / "collect-page"

if COLLECT_PAGE_DIR.exists():
    app.mount(
        "/collect-page",
        StaticFiles(directory=str(COLLECT_PAGE_DIR), html=True),
        name="collect-page",
    )

@app.get("/collect")
def redirect_to_index():
    return RedirectResponse(url="/collect-page/")

# REGISTER PAGE
REGISTER_PAGE_DIR = BASE_DIR / "register-page"

if REGISTER_PAGE_DIR.exists():
    app.mount(
        "/register-page",
        StaticFiles(directory=str(REGISTER_PAGE_DIR), html=True),
        name="register-page",
    )

@app.get("/register")
def redirect_to_index():
    return RedirectResponse(url="/register-page/")

# LEADERBOARD PAGE
LEADERBOARD_PAGE_DIR = BASE_DIR / "leaderboard-page"

if LEADERBOARD_PAGE_DIR.exists():
    app.mount(
        "/leaderboard-page",
        StaticFiles(directory=str(LEADERBOARD_PAGE_DIR), html=True),
        name="leaderboard-page",
    )

@app.get("/leaderboard")
def redirect_to_index():
    return RedirectResponse(url="/leaderboard-page/")

# QUERY PAGE
QUERY_PAGE_DIR = BASE_DIR / "query-page"

if QUERY_PAGE_DIR.exists():
    app.mount(
        "/query-page",
        StaticFiles(directory=str(QUERY_PAGE_DIR), html=True),
        name="query-page",
    )

@app.get("/query")
def redirect_to_index():
    return RedirectResponse(url="/query-page/")

# UPLOAD PAGE
UPLOAD_PAGE_DIR = BASE_DIR / "upload-page"
if UPLOAD_PAGE_DIR.exists():
    app.mount(
        "/upload-page",
        StaticFiles(directory=str(UPLOAD_PAGE_DIR), html=True),
        name="upload-page",
    )

@app.get("/upload", response_class=FileResponse)
async def upload_page(request: Request):
    # Serve the HTML file directly from upload-page/
    file_path = UPLOAD_PAGE_DIR / "index.html"
    return FileResponse(file_path)

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
app.include_router(device_boxes.router)
app.include_router(cases.router)
app.include_router(audit_logs.router)
app.include_router(system.router)
app.include_router(admin_reports.metrics_router)
app.include_router(admin_reports.reports_router)
app.include_router(activity_router.router)

import os
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Create uploads directory if not exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Activity directory for POST /log/activity
ACTIVITY_DIR = os.path.join(BASE_DIR, "activity")
os.makedirs(ACTIVITY_DIR, exist_ok=True)
app.mount("/activity", StaticFiles(directory=ACTIVITY_DIR), name="activity")