"""Tests for config loading from JSON settings."""

from __future__ import annotations

import json
from pathlib import Path

from game import config


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _game_settings() -> dict:
    return json.loads((_project_root() / "game_settings.json").read_text(encoding="utf-8"))


def _building_settings(name: str) -> dict:
    path = _project_root() / "src" / "game" / "settings" / "buildings" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_global_config_values_are_loaded_from_game_settings_json() -> None:
    settings = _game_settings()

    assert config.TICK_MS == settings["timing"]["tick_ms"]
    assert config.WORKER_TILE_TRAVEL_MS == settings["timing"]["worker_tile_travel_ms"]
    assert config.MAX_WORKER_SATIETY == settings["workers"]["satiety"]["max"]
    assert config.SATIETY_DRAIN_PER_GAME_SECOND == settings["workers"]["satiety"]["drain_per_game_second"]
    assert config.TILE_W == settings["world"]["tile_w"]
    assert config.TILE_H == settings["world"]["tile_h"]
    assert config.GRID_SIZE == settings["world"]["grid_size"]
    assert config.WINDOW_SIZE == tuple(settings["window"]["size"])
    assert config.MAX_LEVEL == settings["levels"]["max_level"]
    assert config.TOWN_HALL_STARTING_WAREHOUSE == settings["warehouse_bootstrap"]["town_hall"]
    assert config.TOWN_HALL_MIN_LEVEL_FOR_BUILDING == settings["gates"]["building_min_town_hall_level"]
    assert config.TOWN_HALL_MIN_LEVEL_FOR_HIRE == settings["gates"]["hire_min_town_hall_level"]


def test_building_settings_helpers_read_per_building_json() -> None:
    farm = _building_settings("farm")
    lumber = _building_settings("lumber_camp")
    town_hall = _building_settings("town_hall")

    assert config.building_int_setting("FARM", "work_radius") == farm["work_radius"]
    assert config.building_int_setting("LUMBER_CAMP", "resource_search_radius") == lumber["resource_search_radius"]
    for level, expected in town_hall["housing"]["capacity_by_level"].items():
        assert config.building_level_int_setting("TOWN_HALL", "housing", int(level)) == expected


def test_construction_requirements_are_loaded_from_building_json_levels() -> None:
    school = _building_settings("school")
    configured_levels = school["levels"]
    loaded_levels = config.CONSTRUCTION_REQUIREMENTS["SCHOOL"]

    assert set(loaded_levels) == {int(level) for level in configured_levels}
    for level, payload in configured_levels.items():
        spec = loaded_levels[int(level)]
        assert spec.cost == payload["cost"]
        assert spec.build_time_ms == payload["build_time_ms"]
