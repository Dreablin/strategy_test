"""Geometry helpers for worker placement and target selection."""

from __future__ import annotations

from game.buildings.base import Building
from game.buildings.field import WHEAT_EMPTY, WHEAT_PHASE_4
from game.worker_constants import FARMER_FIELD_RADIUS


def building_center_tile(building: Building) -> tuple[int, int]:
    """Integer grid cell at the footprint center (for stand / orphan position)."""
    pos = building.grid_pos
    if pos is None:
        raise ValueError("building has no grid position")
    gx, gy = pos
    w, h = type(building).footprint
    return gx + w // 2, gy + h // 2


def select_farmer_field_target(
    *,
    farm_home: tuple[int, int],
    field_phases: dict[tuple[int, int], str],
    max_radius: int = FARMER_FIELD_RADIUS,
) -> tuple[int, int] | None:
    """Pick farmer target in priority order: ripe first, then empty."""
    radius = int(max_radius)
    ripe: list[tuple[int, int]] = []
    empty: list[tuple[int, int]] = []
    for tile, phase in field_phases.items():
        if max(abs(int(tile[0]) - int(farm_home[0])), abs(int(tile[1]) - int(farm_home[1]))) > radius:
            continue
        norm = str(phase).upper()
        if norm == WHEAT_PHASE_4:
            ripe.append(tile)
        elif norm == WHEAT_EMPTY:
            empty.append(tile)
    if ripe:
        return min(
            ripe,
            key=lambda t: (
                max(abs(t[0] - farm_home[0]), abs(t[1] - farm_home[1])),
                abs(t[0] - farm_home[0]) + abs(t[1] - farm_home[1]),
                t[0],
                t[1],
            ),
        )
    if empty:
        return min(
            empty,
            key=lambda t: (
                max(abs(t[0] - farm_home[0]), abs(t[1] - farm_home[1])),
                abs(t[0] - farm_home[0]) + abs(t[1] - farm_home[1]),
                t[0],
                t[1],
            ),
        )
    return None


def town_hall_spawn_tile(building: Building) -> tuple[int, int]:
    """Deterministic spawn tile: one cell directly below Town Hall footprint."""
    pos = building.grid_pos
    if pos is None:
        raise ValueError("building has no grid position")
    gx, gy = pos
    w, h = type(building).footprint
    return gx + w // 2, gy + h
