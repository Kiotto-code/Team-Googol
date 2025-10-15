"""Utilities for recording administrative audit events."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .. import models


def record_audit(
    db: Session,
    *,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    metadata: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Persist an audit log entry describing an administrative action."""

    log = models.AuditLog(
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata=metadata or {},
    )
    db.add(log)
    return log


def log_user_event(
    db: Session,
    *,
    actor_id: int,
    action: str,
    user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Record an audit event for a user entity."""

    return record_audit(
        db,
        actor_id=actor_id,
        action=action,
        entity_type="user",
        entity_id=user_id,
        metadata=metadata,
    )


def log_item_event(
    db: Session,
    *,
    actor_id: int,
    action: str,
    item_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Record an audit event for an item entity."""

    return record_audit(
        db,
        actor_id=actor_id,
        action=action,
        entity_type="item",
        entity_id=item_id,
        metadata=metadata,
    )


def log_box_event(
    db: Session,
    *,
    actor_id: int,
    action: str,
    box_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Record an audit event for a box entity."""

    return record_audit(
        db,
        actor_id=actor_id,
        action=action,
        entity_type="box",
        entity_id=box_id,
        metadata=metadata,
    )


def log_case_event(
    db: Session,
    *,
    actor_id: int,
    action: str,
    case_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Record an audit event for a case entity."""

    return record_audit(
        db,
        actor_id=actor_id,
        action=action,
        entity_type="case",
        entity_id=case_id,
        metadata=metadata,
    )
