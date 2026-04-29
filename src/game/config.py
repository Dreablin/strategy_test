"""Global game configuration loaded from JSON with safe defaults."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

_DEFAULT_SETTINGS: dict = {
    "timing": {"tick_ms": 10_000, "worker_tile_travel_ms": 3_000},
    "world": {
        "tile_w": 64,
        "tile_h": 32,
        "grid_size": 32,
        "gather_resource_search_radius": 20,
    },
    "window": {"size": [1280, 720]},
    "warehouse_bootstrap": {
        "town_hall": {"wheat": 200, "wood": 200, "stone": 0, "iron": 0, "boards": 0},
    },
    "gates": {
        "building_min_town_hall_level": {
            "STONE_MINE": 1,
            "IRON_MINE": 1,
            "FORESTER_HUT": 1,
            "SCHOOL": 1,
            "HOUSE": 1,
        },
        "hire_min_town_hall_level": {
            "LUMBERJACK": 1,
            "STONECUTTER": 1,
            "MINER": 1,
            "FARMER": 1,
            "CARRIER": 1,
            "BUILDER": 1,
        },
    },
    "levels": {"max_level": 10},
}


def _deep_update(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _load_settings() -> dict:
    settings = deepcopy(_DEFAULT_SETTINGS)
    project_root = Path(__file__).resolve().parents[2]
    path = project_root / "game_settings.json"
    if not path.exists():
        return settings
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return settings
    if isinstance(loaded, dict):
        return _deep_update(settings, loaded)
    return settings


SETTINGS = _load_settings()

TICK_MS = int(SETTINGS["timing"]["tick_ms"])
WORKER_TILE_TRAVEL_MS = int(SETTINGS["timing"]["worker_tile_travel_ms"])
TILE_W = int(SETTINGS["world"]["tile_w"])
TILE_H = int(SETTINGS["world"]["tile_h"])
GRID_SIZE = int(SETTINGS["world"]["grid_size"])
GATHER_RESOURCE_SEARCH_RADIUS = int(SETTINGS["world"].get("gather_resource_search_radius", 20))


def town_hall_origin_tile() -> tuple[int, int]:
    """Top-left grid tile for the initial 3×3 Town Hall (centred on the map)."""
    mid = GRID_SIZE // 2
    return (mid - 1, mid - 1)


def town_hall_footprint_tiles() -> set[tuple[int, int]]:
    gx0, gy0 = town_hall_origin_tile()
    return {(x, y) for y in range(gy0, gy0 + 3) for x in range(gx0, gx0 + 3)}


def near_town_hall_tile(dx: int = 6, dy: int = 6) -> tuple[int, int]:
    """Grass anchor offset from Town Hall — used by many tests and smoke checks."""
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
