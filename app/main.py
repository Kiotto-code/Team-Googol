from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .db import engine, Base
from sqlalchemy import text
from .routers import users, items, boxes, cases

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
    # Ensure check constraint exists (SQLite doesn't support adding named check constraints easily)
    # As a fallback, create a trigger to enforce allowed values on insert/update
    triggers = conn.execute(text("SELECT name FROM sqlite_master WHERE type='trigger' AND name IN ('trg_users_role_insert','trg_users_role_update')")).fetchall()
    trigger_names = {row[0] for row in triggers}
    if 'trg_users_role_insert' not in trigger_names:
        conn.execute(text(
            """
            CREATE TRIGGER IF NOT EXISTS trg_users_role_insert
            BEFORE INSERT ON users
            FOR EACH ROW
            BEGIN
                SELECT CASE WHEN NEW.role NOT IN ('user','admin') THEN
                    RAISE(ABORT, 'Invalid role value')
                END;
            END;
            """
        ))
    if 'trg_users_role_update' not in trigger_names:
        conn.execute(text(
            """
            CREATE TRIGGER IF NOT EXISTS trg_users_role_update
            BEFORE UPDATE OF role ON users
            FOR EACH ROW
            BEGIN
                SELECT CASE WHEN NEW.role NOT IN ('user','admin') THEN
                    RAISE(ABORT, 'Invalid role value')
                END;
            END;
            """
        ))

openapi_tags = [
    {"name": "admin-users", "description": "Administrative user management endpoints."},
    {"name": "users", "description": "Public user registration and login endpoints."},
    {"name": "admin-items", "description": "Administrative item management endpoints."},
    {"name": "items", "description": "Public item discovery endpoints."},
    {"name": "admin-boxes", "description": "Administrative storage box management."},
    {"name": "admin-cases", "description": "Administrative case tracking endpoints."},
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

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Include API routers
app.include_router(users.admin_router)
app.include_router(users.public_router)
app.include_router(items.admin_router)
app.include_router(items.public_router)
app.include_router(boxes.router)
app.include_router(cases.router)
