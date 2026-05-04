"""Global game configuration loaded from JSON files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_RESOURCE_KEYS: tuple[str, ...] = (
    "wheat",
    "wood",
    "stone",
    "iron",
    "boards",
    "flour",
    "bread",
    "water",
    "chicken",
)


@dataclass(frozen=True, slots=True)
class ConstructionSpec:
    cost: dict[str, int]
    build_time_ms: int


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json_object(path: Path) -> dict:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return loaded


def _load_settings() -> dict:
    path = _project_root() / "game_settings.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing required settings file: {path}")
    return _load_json_object(path)


SETTINGS = _load_settings()

TICK_MS = int(SETTINGS["timing"]["tick_ms"])
WORKER_TILE_TRAVEL_MS = int(SETTINGS["timing"]["worker_tile_travel_ms"])
TILE_W = int(SETTINGS["world"]["tile_w"])
TILE_H = int(SETTINGS["world"]["tile_h"])
GRID_SIZE = int(SETTINGS["world"]["grid_size"])
GATHER_RESOURCE_SEARCH_RADIUS = int(SETTINGS["world"].get("gather_resource_search_radius", 20))


def town_hall_origin_tile() -> tuple[int, int]:
    """Top-left grid tile for the initial 3x3 Town Hall."""
    mid = GRID_SIZE // 2
    return (mid - 1, mid - 1)


def town_hall_footprint_tiles() -> set[tuple[int, int]]:
    gx0, gy0 = town_hall_origin_tile()
    return {(x, y) for y in range(gy0, gy0 + 3) for x in range(gx0, gx0 + 3)}


def near_town_hall_tile(dx: int = 6, dy: int = 6) -> tuple[int, int]:
    """Grass anchor offset from Town Hall."""
    x0, y0 = town_hall_origin_tile()
    return (x0 + dx, y0 + dy)


WINDOW_SIZE = tuple(SETTINGS["window"]["size"])
MAX_LEVEL = int(SETTINGS["levels"]["max_level"])

TOWN_HALL_STARTING_WAREHOUSE = dict(SETTINGS["warehouse_bootstrap"]["town_hall"])

TOWN_HALL_MIN_LEVEL_FOR_BUILDING = {
    k: int(v) for k, v in SETTINGS["gates"]["building_min_town_hall_level"].items()
}
TOWN_HALL_MIN_LEVEL_FOR_HIRE = {
    k: int(v) for k, v in SETTINGS["gates"]["hire_min_town_hall_level"].items()
}


def _load_construction_requirements() -> dict[str, dict[int, ConstructionSpec]]:
    project_root = _project_root()
    buildings_dir = project_root / "src" / "game" / "settings" / "buildings"
    if not buildings_dir.exists():
        raise FileNotFoundError(f"Missing required settings directory: {buildings_dir}")

    result: dict[str, dict[int, ConstructionSpec]] = {}
    for path in sorted(buildings_dir.glob("*.json")):
        payload = _load_json_object(path)
        b_type = str(payload.get("building_type", path.stem)).upper()
        raw_levels = payload.get("levels")
        if not isinstance(raw_levels, dict) or not raw_levels:
            raise ValueError(f"construction entry for {b_type!r} must define levels")

        by_level: dict[int, ConstructionSpec] = {}
        for level_key, level_payload in raw_levels.items():
            if not isinstance(level_payload, dict):
                raise ValueError(f"construction level {level_key!r} for {b_type!r} must be an object")
            cost_raw = level_payload.get("cost")
            if not isinstance(cost_raw, dict):
                raise ValueError(f"construction level {level_key!r} for {b_type!r} must define cost")

            cost = {
                str(name).lower(): max(0, int(amount))
                for name, amount in cost_raw.items()
                if str(name).lower() in _RESOURCE_KEYS
            }
            build_time_ms = max(1, int(level_payload.get("build_time_ms", 1)))
            by_level[int(level_key)] = ConstructionSpec(cost=cost, build_time_ms=build_time_ms)

        result[b_type] = by_level
    return result


CONSTRUCTION_REQUIREMENTS: dict[str, dict[int, ConstructionSpec]] = _load_construction_requirements()
