"""Service layer exports with lazy loading."""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Dict

__all__ = [
    "audit",
    "auth",
    "boxes",
    "cases",
    "idempotency",
    "items",
    "telemetry",
]

_CACHE: Dict[str, ModuleType] = {}


def __getattr__(name: str) -> ModuleType:
    if name in _CACHE:
        return _CACHE[name]
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        _CACHE[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
