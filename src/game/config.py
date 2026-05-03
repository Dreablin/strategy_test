"""Global game configuration loaded from JSON with safe defaults."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

_RESOURCE_KEYS: tuple[str, ...] = ("wheat", "wood", "stone", "iron", "boards", "flour", "bread", "water")


@dataclass(frozen=True, slots=True)
class ConstructionSpec:
    cost: dict[str, int]
    build_time_ms: int


def _scaled_levels(base_cost: dict[str, int], base_time_ms: int) -> dict[str, dict]:
    levels: dict[str, dict] = {}
    for level in range(1, 11):
        multiplier = 1.0 + (level - 1) * 0.2
        cost = {k: int(round(v * multiplier)) for k, v in base_cost.items()}
        levels[str(level)] = {"cost": cost, "build_time_ms": int(round(base_time_ms * multiplier))}
    return levels


def _construction_fallback_defaults() -> dict[str, dict]:
    return {
        "LUMBER_CAMP": {"levels": _scaled_levels({"wood": 12, "stone": 4}, 30_000)},
        "STONE_MINE": {"levels": _scaled_levels({"wood": 10, "stone": 8}, 34_000)},
        "IRON_MINE": {"levels": _scaled_levels({"wood": 10, "stone": 10, "iron": 2}, 38_000)},
        "FARM": {"levels": _scaled_levels({"wood": 8, "stone": 3, "wheat": 2}, 26_000)},
        "FORESTER_HUT": {"levels": _scaled_levels({"wood": 9, "stone": 3}, 28_000)},
        "SCHOOL": {"levels": _scaled_levels({"wood": 14, "stone": 8, "boards": 4}, 40_000)},
        "HOUSE": {"levels": _scaled_levels({"wood": 12, "stone": 6, "boards": 2}, 36_000)},
        "MILL": {"levels": _scaled_levels({"wood": 2}, 30_000)},
        "BAKERY": {"levels": _scaled_levels({"wood": 8, "stone": 4, "boards": 2}, 36_000)},
        "WELL": {"levels": {"1": {"cost": {"wood": 1, "boards": 2}, "build_time_ms": 12_000}}},
    }


def _default_construction_from_files() -> dict[str, dict]:
    project_root = Path(__file__).resolve().parents[2]
    buildings_dir = project_root / "src" / "game" / "settings" / "buildings"
    if not buildings_dir.exists():
        return _construction_fallback_defaults()
    result: dict[str, dict] = {}
    for path in sorted(buildings_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        b_type = str(payload.get("building_type", path.stem)).upper()
        if not b_type:
            continue
        if isinstance(payload.get("levels"), dict):
            result[b_type] = {"levels": payload["levels"]}
    if result:
        return result
    return _construction_fallback_defaults()


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
        "town_hall": {"wheat": 200, "wood": 200, "stone": 0, "iron": 0, "boards": 0, "flour": 0, "bread": 0},
    },
    "construction": _default_construction_from_files(),
    "gates": {
        "building_min_town_hall_level": {
            "STONE_MINE": 1,
            "IRON_MINE": 1,
            "FORESTER_HUT": 1,
            "SCHOOL": 1,
            "HOUSE": 1,
            "BAKERY": 1,
            "WELL": 1,
        },
        "hire_min_town_hall_level": {
            "LUMBERJACK": 1,
            "STONECUTTER": 1,
            "MINER": 1,
            "FARMER": 1,
            "CARRIER": 1,
            "BUILDER": 1,
            "SAWYER": 1,
            "MILLER": 1,
            "BAKER": 1,
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


def _load_construction_requirements() -> dict[str, dict[int, ConstructionSpec]]:
    raw = SETTINGS.get("construction", {})
    result: dict[str, dict[int, ConstructionSpec]] = {}
    if not isinstance(raw, dict):
        return result
    for b_type, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        raw_levels = payload.get("levels", {})
        if not isinstance(raw_levels, dict):
            continue
        by_level: dict[int, ConstructionSpec] = {}
        for level_key, level_payload in raw_levels.items():
            if not isinstance(level_payload, dict):
                continue
            cost_raw = level_payload.get("cost", {})
            if not isinstance(cost_raw, dict):
                continue
            cost = {
                str(name).lower(): max(0, int(amount))
                for name, amount in cost_raw.items()
                if str(name).lower() in _RESOURCE_KEYS
            }
            build_time_ms = max(1, int(level_payload.get("build_time_ms", 1)))
            by_level[int(level_key)] = ConstructionSpec(cost=cost, build_time_ms=build_time_ms)
        if by_level:
            result[str(b_type)] = by_level
    return result


CONSTRUCTION_REQUIREMENTS: dict[str, dict[int, ConstructionSpec]] = _load_construction_requirements()
