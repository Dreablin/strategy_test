"""Construction and upgrade costs (PRD §3 F-BLD-04 / F-BLD-05)."""

from game.config import BUILD_COST_WOOD


def build_cost(building_type: str) -> dict[str, int]:
    """Cost to place a new level-1 building (always 100 wood)."""
    _ = building_type
    return {"wood": BUILD_COST_WOOD}


def upgrade_cost(current_level: int) -> dict[str, int]:
    """Cost to upgrade from *current_level* to *current_level* + 1 (levels 1–9 only)."""
    if not isinstance(current_level, int) or current_level < 1 or current_level > 10:
        raise ValueError("current_level must be between 1 and 10")
    if current_level >= 10:
        raise ValueError("cannot upgrade beyond max level")

    next_level = current_level + 1
    cost: dict[str, int] = {"wood": 100 * next_level}

    if next_level >= 5:
        cost["stone"] = 200 * (next_level - 4)
    if next_level >= 7:
        cost["iron"] = 300 * (next_level - 6)

    return cost
