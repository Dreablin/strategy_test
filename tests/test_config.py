"""Tests for config loading from JSON settings."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
    assert config.HUNGER_SATIETY_THRESHOLD == settings["workers"]["satiety"]["hunger_threshold"]
    assert config.TILE_W == settings["world"]["tile_w"]
    assert config.TILE_H == settings["world"]["tile_h"]
    selected = settings["world"]["selected_map_size"]
    selected_map = settings["world"]["map_sizes"][selected]
    assert config.SELECTED_MAP_SIZE == selected
    assert config.GRID_SIZE == selected_map["grid_size"]
    assert config.WORLD_RESOURCE_SETTINGS == selected_map["resources"]
    assert config.WINDOW_SIZE == tuple(settings["window"]["size"])
    assert config.MAX_LEVEL == settings["levels"]["max_level"]
    assert config.TOWN_HALL_STARTING_WAREHOUSE == settings["warehouse_bootstrap"]["town_hall"]
    assert config.TOWN_HALL_MIN_LEVEL_FOR_BUILDING == settings["gates"]["building_min_town_hall_level"]
    assert config.TOWN_HALL_MIN_LEVEL_FOR_HIRE == settings["gates"]["hire_min_town_hall_level"]


def test_world_map_size_presets_are_available_from_game_settings_json() -> None:
    settings = _game_settings()
    presets = settings["world"]["map_sizes"]

    assert settings["world"]["selected_map_size"] == "medium"
    assert set(presets) == {"small", "medium", "large"}
    assert presets["small"]["grid_size"] == 70
    assert presets["medium"]["grid_size"] == 110
    assert presets["large"]["grid_size"] == 220
    assert presets["small"]["resources"]["stone_center_count"] < presets["medium"]["resources"]["stone_center_count"]
    assert presets["medium"]["resources"]["stone_center_count"] < presets["large"]["resources"]["stone_center_count"]
    assert presets["small"]["resources"]["tree_grove_count"] < presets["medium"]["resources"]["tree_grove_count"]
    assert presets["medium"]["resources"]["tree_grove_count"] < presets["large"]["resources"]["tree_grove_count"]


def test_building_settings_helpers_read_per_building_json() -> None:
    farm = _building_settings("farm")
    lumber = _building_settings("lumber_camp")
    town_hall = _building_settings("town_hall")

    assert config.building_int_setting("FARM", "work_radius") == farm["work_radius"]
    assert config.building_int_setting("FARM", "work", "action_ms") == farm["work"]["action_ms"]
    assert config.building_int_setting("LUMBER_CAMP", "resource_search_radius") == lumber["resource_search_radius"]
    assert config.building_int_setting("LUMBER_CAMP", "work", "rest_ms") == lumber["work"]["rest_ms"]
    for level, expected in town_hall["housing"]["capacity_by_level"].items():
        assert config.building_level_int_setting("TOWN_HALL", "housing", int(level)) == expected


def test_building_worker_effects_read_assigned_worker_effects_from_building_json() -> None:
    lumber = _building_settings("lumber_camp")
    expected = lumber["worker_effects"]["by_level"]["5"]["assigned_worker"]

    assert config.building_worker_effects("LUMBER_CAMP", 1) == {}
    assert config.building_worker_effects("LUMBER_CAMP", 5) == expected
    assert config.building_worker_effects("TOWN_HALL", 5) == {}


def test_configured_worker_effect_sources_read_global_and_worker_type_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {
                "global": {"move_speed_mult": 0.05},
                "by_type": {"CARRIER": {"gather_speed_mult": -0.10}},
            },
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)

    assert config.configured_worker_effect_sources("carrier") == [
        (config.GLOBAL_WORKER_EFFECT_SOURCE, {"move_speed_mult": 0.05}),
        (config.worker_type_effect_source("CARRIER"), {"gather_speed_mult": -0.10}),
    ]
    assert config.configured_worker_effect_sources("builder") == [
        (config.GLOBAL_WORKER_EFFECT_SOURCE, {"move_speed_mult": 0.05}),
    ]
    assert config.configured_worker_effect_source_keys("carrier") == (
        config.GLOBAL_WORKER_EFFECT_SOURCE,
        config.worker_type_effect_source("CARRIER"),
    )


def test_building_worker_effects_validate_stats_and_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        config.BUILDING_SETTINGS,
        "TEST_BAD_STAT",
        {
            "worker_effects": {
                "by_level": {
                    "1": {"assigned_worker": {"unknown_stat": 0.1}},
                }
            }
        },
    )
    with pytest.raises(ValueError, match="unknown worker effect stat"):
        config.building_worker_effects("TEST_BAD_STAT", 1)

    monkeypatch.setitem(
        config.BUILDING_SETTINGS,
        "TEST_BAD_VALUE",
        {
            "worker_effects": {
                "by_level": {
                    "1": {"assigned_worker": {"move_speed_mult": "fast"}},
                }
            }
        },
    )
    with pytest.raises(ValueError, match="must be numeric"):
        config.building_worker_effects("TEST_BAD_VALUE", 1)


def test_configured_worker_effect_sources_validate_stats_and_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {"global": {"unknown_stat": 0.05}, "by_type": {}},
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)
    with pytest.raises(ValueError, match="unknown worker effect stat"):
        config.configured_worker_effect_sources("CARRIER")

    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {"global": {}, "by_type": {"CARRIER": {"move_speed_mult": "fast"}}},
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)
    with pytest.raises(ValueError, match="must be numeric"):
        config.configured_worker_effect_sources("CARRIER")


def test_construction_requirements_are_loaded_from_building_json_levels() -> None:
    school = _building_settings("school")
    configured_levels = school["levels"]
    loaded_levels = config.CONSTRUCTION_REQUIREMENTS["SCHOOL"]

    assert set(loaded_levels) == {int(level) for level in configured_levels}
    for level, payload in configured_levels.items():
        spec = loaded_levels[int(level)]
        assert spec.cost == payload["cost"]
        assert spec.build_time_ms == payload["build_time_ms"]
