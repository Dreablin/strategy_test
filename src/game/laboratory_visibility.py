"""Laboratory presence helpers for UI gating."""

from __future__ import annotations

from typing import Any

_LABORATORY_TAG = "LABORATORY"


def has_completed_laboratory(registry: Any) -> bool:
    """True when a built (non-under-construction) Laboratory exists."""
    buildings = getattr(registry, "all", None)
    if not callable(buildings):
        return False
    for building in buildings():
        if building.type_tag == _LABORATORY_TAG and not building.is_under_construction:
            return True
    return False
