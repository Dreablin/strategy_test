"""Construction and upgrade costs."""

from game.config import BUILD_COSTS, UPGRADE_COSTS


def build_cost(building_type: str) -> dict[str, int]:
    """Cost to place a new level-1 building."""
    key = building_type.upper().replace(" ", "_")
    return dict(BUILD_COSTS.get(key, BUILD_COSTS.get("LUMBER_CAMP", {"wood": 5})))


def upgrade_cost(building_type: str | int, current_level: int | None = None) -> dict[str, int]:
    """Cost to upgrade from *current_level* to *current_level* + 1.

    Backward compatibility:
    - upgrade_cost(level) -> uses DEFAULT table
    - upgrade_cost(type_tag, level) -> per-building table with DEFAULT fallback
    """
    if current_level is None:
        b_type = "DEFAULT"
        current = int(building_type)
    else:
        b_type = str(building_type).upper().replace(" ", "_")
        current = int(current_level)

    table = UPGRADE_COSTS.get(b_type, UPGRADE_COSTS.get("DEFAULT", {}))

    # Infer max level from the highest configured "next level".
    configured_next_levels = [int(k) for k in table.keys()] if table else []
    max_level = max(configured_next_levels) if configured_next_levels else 10

    # current must be in [1, max_level - 1]
    if not isinstance(current, int) or current < 1 or current > max_level:
        raise ValueError("current_level must be between 1 and configured max level")
    if current >= max_level:
        raise ValueError("cannot upgrade beyond max level")

    next_level = current + 1
    key = str(next_level)
    if key not in table:
        raise ValueError("upgrade cost not configured for next level")
    return dict(table[key])
