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
    "economy": {
        "initial_resources": {"food": 200, "wood": 200, "stone": 0, "iron": 0},
        "build_costs": {
            "LUMBER_CAMP": {"wood": 5},
            "STONE_MINE": {"wood": 5},
            "IRON_MINE": {"wood": 5},
            "FARM": {"wood": 5},
        },
        "upgrade_costs": {
            "DEFAULT": {
                "2": {"wood": 5},
                "3": {"wood": 5},
                "4": {"wood": 5},
                "5": {"wood": 5, "stone": 5},
                "6": {"wood": 5, "stone": 5},
                "7": {"wood": 5, "stone": 5, "iron": 5},
                "8": {"wood": 5, "stone": 5, "iron": 5},
                "9": {"wood": 5, "stone": 5, "iron": 5},
                "10": {"wood": 5, "stone": 5, "iron": 5},
            }
        },
        "worker_hire_costs": {
            "LUMBERJACK": {"food": 5},
            "STONECUTTER": {"food": 5},
            "MINER": {"food": 5},
            "FARMER": {"food": 5},
        },
    },
    "gates": {
        "building_min_town_hall_level": {"STONE_MINE": 3, "IRON_MINE": 5},
        "hire_min_town_hall_level": {"LUMBERJACK": 1, "STONECUTTER": 3, "MINER": 5, "FARMER": 1},
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
WINDOW_SIZE = tuple(SETTINGS["window"]["size"])
MAX_LEVEL = int(SETTINGS["levels"]["max_level"])

INITIAL_RESOURCES = dict(SETTINGS["economy"]["initial_resources"])
BUILD_COSTS = {k: dict(v) for k, v in SETTINGS["economy"]["build_costs"].items()}
UPGRADE_COSTS = {
    b_type: {str(level): dict(cost) for level, cost in levels.items()}
    for b_type, levels in SETTINGS["economy"]["upgrade_costs"].items()
}
WORKER_HIRE_COSTS = {k: dict(v) for k, v in SETTINGS["economy"]["worker_hire_costs"].items()}

TOWN_HALL_MIN_LEVEL_FOR_BUILDING = {
    k: int(v) for k, v in SETTINGS["gates"]["building_min_town_hall_level"].items()
}
TOWN_HALL_MIN_LEVEL_FOR_HIRE = {
    k: int(v) for k, v in SETTINGS["gates"]["hire_min_town_hall_level"].items()
}

# Backward-compat aliases used by existing tests and UI code.
WORKER_HIRE_COST = dict(WORKER_HIRE_COSTS["LUMBERJACK"])
BUILD_COST_WOOD = int(BUILD_COSTS["LUMBER_CAMP"]["wood"])
