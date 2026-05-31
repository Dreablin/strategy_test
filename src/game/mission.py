"""Mission completion helpers."""

from __future__ import annotations

from typing import Any


def statue_completed(registry: Any) -> bool:
    if registry is None:
        return False
    for building in registry.all():
        if getattr(building, "type_tag", "") != "STATUE":
            continue
        complete = getattr(building, "mission_complete", False)
        if bool(complete):
            return True
    return False
