from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..dependencies.auth import require_roles

router = APIRouter(
    prefix="/api/v1/admin/audit-logs",
    tags=["admin-audit-logs"],
    dependencies=[Depends(require_roles("admin", "staff"))],
)


@router.get("/", response_model=schemas.PaginatedAuditLogs)
def list_audit_logs(
    db: Session = Depends(get_db),
    *,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    actor_user_id: Annotated[int | None, Query()] = None,
    entity_type: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
) -> schemas.PaginatedAuditLogs:
    """Return audit log entries filtered by the requested criteria."""

    query = db.query(models.AuditLog)

    if actor_user_id is not None:
        query = query.filter(models.AuditLog.actor_user_id == actor_user_id)
    if entity_type:
        query = query.filter(models.AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(models.AuditLog.action == action)
    if created_from:
        query = query.filter(models.AuditLog.created_at >= created_from)
    if created_to:
        query = query.filter(models.AuditLog.created_at <= created_to)

    total = query.count()
    total_pages = (total + limit - 1) // limit if total else 0

    if page > 1 and (page - 1) * limit >= total and total != 0:
        raise HTTPException(status_code=400, detail="Page out of range")

    entries = (
        query.order_by(models.AuditLog.created_at.desc(), models.AuditLog.audit_id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return schemas.PaginatedAuditLogs(
        data=entries,
        meta=schemas.PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )
