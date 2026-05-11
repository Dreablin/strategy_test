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
    "beef",
    "hide",
)
WORKER_EFFECT_STATS: tuple[str, ...] = ("move_speed_mult", "gather_speed_mult")
GLOBAL_WORKER_EFFECT_SOURCE = ("global", "all_workers")


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


def _load_building_settings() -> dict[str, dict]:
    project_root = _project_root()
    buildings_dir = project_root / "src" / "game" / "settings" / "buildings"
    if not buildings_dir.exists():
        raise FileNotFoundError(f"Missing required settings directory: {buildings_dir}")

    result: dict[str, dict] = {}
    for path in sorted(buildings_dir.glob("*.json")):
        payload = _load_json_object(path)
        b_type = str(payload.get("building_type", path.stem)).upper()
        result[b_type] = payload
    return result


BUILDING_SETTINGS = _load_building_settings()

TICK_MS = int(SETTINGS["timing"]["tick_ms"])
WORKER_TILE_TRAVEL_MS = int(SETTINGS["timing"]["worker_tile_travel_ms"])
MAX_WORKER_SATIETY = int(SETTINGS["workers"]["satiety"]["max"])
SATIETY_DRAIN_PER_GAME_SECOND = int(SETTINGS["workers"]["satiety"]["drain_per_game_second"])
TILE_W = int(SETTINGS["world"]["tile_w"])
TILE_H = int(SETTINGS["world"]["tile_h"])
GRID_SIZE = int(SETTINGS["world"]["grid_size"])


def building_setting(type_tag: str, *keys: str) -> object:
    """Return a required setting value from a per-building JSON file."""
    current: object = BUILDING_SETTINGS[str(type_tag).upper()]
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            joined = ".".join((str(type_tag).upper(), *keys))
            raise KeyError(f"Missing building setting: {joined}")
        current = current[key]
    return current


def building_int_setting(type_tag: str, *keys: str) -> int:
    return int(building_setting(type_tag, *keys))


def building_level_int_setting(type_tag: str, section: str, level: int) -> int:
    payload = building_setting(type_tag, section)
    if not isinstance(payload, dict) or "capacity_by_level" not in payload:
        raise KeyError(f"Missing level settings for {str(type_tag).upper()}.{section}")
    by_level = payload["capacity_by_level"]
    if not isinstance(by_level, dict):
        raise ValueError(f"{str(type_tag).upper()}.{section}.capacity_by_level must be an object")
    key = str(max(1, int(level)))
    if key not in by_level:
        raise KeyError(f"Missing level setting for {str(type_tag).upper()}.{section}.level {key}")
    return int(by_level[key])


def _validate_worker_effect_mapping(label: str, payload: object) -> dict[str, float]:
    if payload in ({}, None):
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    result: dict[str, float] = {}
    for stat, value in payload.items():
        key = str(stat)
        if key not in WORKER_EFFECT_STATS:
            raise ValueError(f"unknown worker effect stat: {key}")
        if not isinstance(value, (int, float)):
            raise ValueError(f"worker effect {key} must be numeric")
        result[key] = float(value)
    return result


def worker_type_effect_source(worker_type: str) -> tuple[str, str]:
    return ("worker_type", str(worker_type).upper())


def configured_worker_effect_source_keys(worker_type: str) -> tuple[tuple[str, str], ...]:
    return (GLOBAL_WORKER_EFFECT_SOURCE, worker_type_effect_source(worker_type))


def configured_worker_effect_sources(worker_type: str) -> list[tuple[tuple[str, str], dict[str, float]]]:
    """Return global and worker-type effect deltas configured in game settings."""
    effects = SETTINGS.get("workers", {}).get("effects", {})
    if effects in ({}, None):
        return []
    if not isinstance(effects, dict):
        raise ValueError("workers.effects must be an object")
    result: list[tuple[tuple[str, str], dict[str, float]]] = []

    global_effects = _validate_worker_effect_mapping("workers.effects.global", effects.get("global", {}))
    if global_effects:
        result.append((GLOBAL_WORKER_EFFECT_SOURCE, global_effects))

    by_type = effects.get("by_type", {})
    if by_type in ({}, None):
        return result
    if not isinstance(by_type, dict):
        raise ValueError("workers.effects.by_type must be an object")
    type_tag = str(worker_type).upper()
    type_effects = _validate_worker_effect_mapping(
        f"workers.effects.by_type.{type_tag}",
        by_type.get(type_tag, {}),
    )
    if type_effects:
        result.append((worker_type_effect_source(type_tag), type_effects))
    return result


def building_worker_effects(
    type_tag: str,
    level: int,
    *,
    scope: str = "assigned_worker",
) -> dict[str, float]:
    """Return configured worker stat deltas for a building level/scope.

    Missing ``worker_effects`` sections are valid and mean "no effects".
    """
    payload = BUILDING_SETTINGS.get(str(type_tag).upper(), {})
    if not isinstance(payload, dict):
        return {}
    effects = payload.get("worker_effects", {})
    if effects in ({}, None):
        return {}
    if not isinstance(effects, dict):
        raise ValueError(f"{str(type_tag).upper()}.worker_effects must be an object")
    by_level = effects.get("by_level", {})
    if by_level in ({}, None):
        return {}
    if not isinstance(by_level, dict):
        raise ValueError(f"{str(type_tag).upper()}.worker_effects.by_level must be an object")
    level_payload = by_level.get(str(max(1, int(level))), {})
    if level_payload in ({}, None):
        return {}
    if not isinstance(level_payload, dict):
        raise ValueError(
            f"{str(type_tag).upper()}.worker_effects.by_level.{int(level)} must be an object"
        )
    scoped = level_payload.get(scope, {})
    if scoped in ({}, None):
        return {}
    if not isinstance(scoped, dict):
        raise ValueError(
            f"{str(type_tag).upper()}.worker_effects.by_level.{int(level)}.{scope} must be an object"
        )
    return _validate_worker_effect_mapping(
        f"{str(type_tag).upper()}.worker_effects.by_level.{int(level)}.{scope}",
        scoped,
    )


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
        if raw_levels is None:
            continue
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
