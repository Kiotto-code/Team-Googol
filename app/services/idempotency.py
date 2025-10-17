"""Helpers for enforcing idempotent requests."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models


def build_scope(box_id: int, action: str) -> str:
    return f"box:{box_id}:{action}"


def find_entry(db: Session, *, scope: str, key: str) -> models.IdempotencyKey | None:
    return (
        db.query(models.IdempotencyKey)
        .filter(models.IdempotencyKey.scope == scope, models.IdempotencyKey.key == key)
        .one_or_none()
    )


def claim_key(db: Session, *, scope: str, key: str) -> models.IdempotencyKey:
    existing = find_entry(db, scope=scope, key=key)
    if existing:
        if existing.response_code is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another request with the same idempotency key is in progress",
            )
        return existing

    entry = models.IdempotencyKey(scope=scope, key=key)
    db.add(entry)
    db.flush()
    return entry


def finalize_key(
    entry: models.IdempotencyKey,
    *,
    response_code: int,
    response_body: Any,
) -> None:
    entry.response_code = response_code
    entry.response_body = json.dumps(response_body, default=str)
