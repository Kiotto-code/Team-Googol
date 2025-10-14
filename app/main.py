from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .db import engine, Base
from .routers import users, items, boxes, cases

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team-Googol Lost & Found API",
    version="0.1.0",
    description=(
        "Simple Lost & Found backend with SQLite. Use Swagger UI at /docs to try endpoints "
        "directly from the browser."
    ),
)

# Static and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Include API routers
app.include_router(users.router)
app.include_router(items.router)
app.include_router(boxes.router)
app.include_router(cases.router)
