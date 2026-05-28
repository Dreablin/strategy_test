"""Geometry helpers for worker placement and target selection."""

from __future__ import annotations

from collections.abc import Collection

from game.buildings.base import Building
from game.buildings.field import WHEAT_EMPTY, WHEAT_PHASE_4
from game.worker_constants import FARMER_FIELD_RADIUS


def worker_inside_building_footprint(worker: object, building: Building) -> bool:
    """True when the worker's current tile lies inside the building footprint."""
    pos = building.grid_pos
    if pos is None:
        return False
    gx, gy = pos
    w, h = type(building).footprint
    wx, wy = getattr(worker, "current_tile", (0, 0))
    return gx <= wx < gx + w and gy <= wy < gy + h


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


def select_ripe_vineyard_target_tile(
    *,
    farm_home: tuple[int, int],
    ripe_tiles: Collection[tuple[int, int]],
    excluded_tiles: Collection[tuple[int, int]],
    max_radius: int,
) -> tuple[int, int] | None:
    """Pick a ripe vineyard plot tile within Chebyshev radius, excluding reserved tiles.

    Tie-break matches ``select_farmer_field_target`` ripe ordering (closest, then stable).
    """
    hx, hy = int(farm_home[0]), int(farm_home[1])
    radius = int(max_radius)
    blocked = {(int(t[0]), int(t[1])) for t in excluded_tiles}
    in_range: list[tuple[int, int]] = []
    for tx, ty in ripe_tiles:
        tile = (int(tx), int(ty))
        if tile in blocked:
            continue
        if max(abs(tile[0] - hx), abs(tile[1] - hy)) > radius:
            continue
        in_range.append(tile)
    if not in_range:
        return None
    return min(
        in_range,
        key=lambda t: (
            max(abs(t[0] - hx), abs(t[1] - hy)),
            abs(t[0] - hx) + abs(t[1] - hy),
            t[0],
            t[1],
        ),
    )


def town_hall_spawn_tile(building: Building) -> tuple[int, int]:
    """Deterministic spawn tile: one cell directly below Town Hall footprint."""
    pos = building.grid_pos
    if pos is None:
        raise ValueError("building has no grid position")
    gx, gy = pos
    w, h = type(building).footprint
    return gx + w // 2, gy + h
