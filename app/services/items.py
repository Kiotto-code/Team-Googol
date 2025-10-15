"""Service utilities for administrative item workflows."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Final

import numpy as np

from .. import models
from ..db import SessionLocal
from ..utils.clip_utils import get_image_embedding, get_text_embedding

VALID_STATUSES: Final[set[str]] = {
    "uploaded",
    "processing",
    "available",
    "matched",
    "claimed",
    "returned",
    "expired",
    "archived",
}

_ALLOWED_TRANSITIONS: Final[dict[str | None, set[str]]] = {
    None: {"uploaded", "processing", "available"},
    "uploaded": {"processing", "available", "matched", "claimed", "expired", "archived"},
    "processing": {"available", "matched", "claimed", "expired", "archived"},
    "available": {"matched", "claimed", "returned", "expired", "archived"},
    "matched": {"claimed", "returned", "expired", "archived"},
    "claimed": {"returned", "expired", "archived"},
    "returned": {"archived"},
    "expired": {"archived"},
    "archived": set(),
}


def is_valid_status(status: str | None) -> bool:
    """Return True when the provided status is recognised or missing."""

    if status is None:
        return True
    return status in VALID_STATUSES


def is_allowed_transition(current_status: str | None, new_status: str) -> bool:
    """Validate a status transition against the configured matrix."""

    if current_status == new_status:
        return True
    allowed = _ALLOWED_TRANSITIONS.get(current_status)
    if allowed is None:
        return True if not VALID_STATUSES else new_status in VALID_STATUSES
    return new_status in allowed


def _tensor_to_json(tensor) -> str:
    return json.dumps(tensor.detach().cpu().numpy().flatten().tolist())


def refresh_item_embeddings(
    item_id: int,
    *,
    refresh_image: bool = True,
    refresh_description: bool = True,
) -> None:
    """Compute embeddings for an item and persist them."""

    session = SessionLocal()
    try:
        item = session.get(models.Item, item_id)
        if not item or item.deleted_at:
            return

        updated = False

        if refresh_image and item.image_url and os.path.exists(item.image_url):
            try:
                tensor = get_image_embedding(item.image_url)
            except Exception as exc:  # pragma: no cover - side-effect logging
                print(f"[embedding] Failed to compute image embedding for item {item_id}: {exc}")
            else:
                item.image_embedding = _tensor_to_json(tensor)
                updated = True

        description_source = item.description or item.gemini_description
        if refresh_description and description_source:
            try:
                tensor = get_text_embedding(description_source)
            except Exception as exc:  # pragma: no cover - side-effect logging
                print(
                    f"[embedding] Failed to compute text embedding for item {item_id}: {exc}"
                )
            else:
                item.description_embedding = _tensor_to_json(tensor)
                updated = True

        if updated:
            item.updated_at = datetime.utcnow()
            session.add(item)
            session.commit()
        else:
            session.rollback()
    finally:
        session.close()


def parse_embedding(embedding: str | None) -> np.ndarray | None:
    """Deserialize a stored embedding into a normalised numpy vector."""

    if not embedding:
        return None
    try:
        data = json.loads(embedding)
        vector = np.array(data, dtype=np.float32)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if vector.ndim > 1:
        vector = vector.flatten()
    norm = np.linalg.norm(vector)
    if not norm:
        return None
    return vector / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity for already normalised vectors."""

    return float(np.dot(a, b))


__all__ = [
    "VALID_STATUSES",
    "is_valid_status",
    "is_allowed_transition",
    "refresh_item_embeddings",
    "parse_embedding",
    "cosine_similarity",
]
