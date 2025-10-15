"""System level endpoints such as health and readiness probes."""
from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter(prefix="/api/v1", tags=["system"])

_process_start_time = monotonic()


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


@router.get("/healthz")
def healthz() -> JSONResponse:
    """Return a lightweight health status including uptime information."""

    uptime_seconds = monotonic() - _process_start_time
    payload = {
        "status": "ok",
        "timestamp": _utcnow().isoformat(),
        "checks": {"application": True},
        "uptime_seconds": round(uptime_seconds, 2),
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=payload)


@router.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> JSONResponse:
    """Run readiness diagnostics that ensure critical dependencies are reachable."""

    checks: dict[str, dict[str, str | bool]] = {}
    db_status: dict[str, str | bool]
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:  # pragma: no cover - defensive
        db_status = {"healthy": False, "error": str(exc)}
    else:
        db_status = {"healthy": True}
    checks["database"] = db_status

    overall_ready = all(check.get("healthy") for check in checks.values())
    payload = {
        "status": "ready" if overall_ready else "degraded",
        "timestamp": _utcnow().isoformat(),
        "checks": checks,
    }

    http_status = (
        status.HTTP_200_OK if overall_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=http_status, content=payload)

