"""Hardware integration shims for box actions."""
from __future__ import annotations

from datetime import datetime
from random import randint
from typing import Any

from .. import models


class BoxHardwareError(RuntimeError):
    """Raised when a hardware interaction fails."""


async def open_door(box: models.Box) -> dict[str, Any]:
    """Simulate opening a storage box door."""
    message = "Door opened"
    if box.door_status:
        message = "Door already open"
    return {
        "door_status": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def close_door(box: models.Box) -> dict[str, Any]:
    """Simulate closing a storage box door."""
    message = "Door closed"
    if box.door_status is False:
        message = "Door already closed"
    return {
        "door_status": False,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def ping_box(box: models.Box) -> dict[str, Any]:
    """Return synthetic telemetry for a ping request."""
    return {
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat(),
        "door_status": box.door_status,
        "status": box.status,
        "load": box.load,
        "latency_ms": randint(5, 30),
    }
