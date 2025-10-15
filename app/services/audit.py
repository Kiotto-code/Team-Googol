"""Utilities for recording administrative audit events."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from .. import models


def record_audit(
    db: Session,
    *,
    actor_id: int,
    action: str,
    target_user_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Persist an audit log entry describing an administrative action."""

    log = models.AuditLog(
        actor_user_id=actor_id,
        target_user_id=target_user_id,
        action=action,
        payload=json.dumps(payload or {}, default=str),
    )
    db.add(log)
    return log
