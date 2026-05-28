"""Laboratory presence helpers for UI gating."""

from __future__ import annotations

from typing import Any

_LABORATORY_TAG = "LABORATORY"


def has_completed_laboratory(registry: Any) -> bool:
    """True when a built (non-under-construction) Laboratory exists."""
    return completed_laboratory(registry) is not None


def completed_laboratory(registry: Any) -> Any | None:
    """The built Laboratory instance, or ``None`` if none is complete."""
    buildings = getattr(registry, "all", None)
    if not callable(buildings):
        return None
    for building in buildings():
        if building.type_tag == _LABORATORY_TAG and not building.is_under_construction:
            return building
    return None
