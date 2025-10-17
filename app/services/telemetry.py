"""Telemetry helpers and websocket broadcasting."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from sqlalchemy.orm import Session

from .. import models

logger = logging.getLogger(__name__)


class TelemetryManager:
    """Manage websocket subscribers for telemetry events."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        async with self._lock:
            connections = list(self._connections)
        if not connections:
            return
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:  # pragma: no cover - defensive cleanup
                logger.exception("Failed to send telemetry message; dropping connection")
                await self.disconnect(websocket)


def record_telemetry(
    db: Session,
    *,
    box: models.Box,
    payload: dict[str, Any],
) -> models.BoxTelemetry:
    telemetry = models.BoxTelemetry(box=box, payload=payload)
    db.add(telemetry)
    db.flush()
    return telemetry


telemetry_manager = TelemetryManager()
