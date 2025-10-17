"""Domain helpers for case workflows."""
from __future__ import annotations

from typing import Final


DEFAULT_STATUS: Final[str] = "open"
VALID_STATUSES: Final[set[str]] = {
    DEFAULT_STATUS,
    "claimed",
    "retrieved",
    "expired",
    "forfeited",
}
TERMINAL_STATUSES: Final[frozenset[str]] = frozenset({"retrieved", "expired", "forfeited"})

_ALLOWED_TRANSITIONS: Final[dict[str | None, set[str]]] = {
    None: {DEFAULT_STATUS},
    DEFAULT_STATUS: {"claimed", "expired", "forfeited"},
    "claimed": {"retrieved", "expired", "forfeited"},
    "retrieved": set(),
    "expired": set(),
    "forfeited": set(),
}


def is_valid_status(status: str | None) -> bool:
    """Return True if the provided status is recognised or missing."""

    if status is None:
        return True
    return status in VALID_STATUSES


def is_allowed_transition(current: str | None, new: str) -> bool:
    """Check whether a transition is permitted according to the matrix."""

    if current == new:
        return True
    allowed = _ALLOWED_TRANSITIONS.get(current)
    if allowed is None:
        return new in VALID_STATUSES
    return new in allowed


def is_terminal(status: str | None) -> bool:
    """Return True when the status indicates the case is closed."""

    if status is None:
        return False
    return status in TERMINAL_STATUSES


__all__ = [
    "DEFAULT_STATUS",
    "VALID_STATUSES",
    "TERMINAL_STATUSES",
    "is_valid_status",
    "is_allowed_transition",
    "is_terminal",
]
