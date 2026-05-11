"""Tests proving winery.json settings are loaded correctly (T345)."""

from __future__ import annotations

from game.config import building_int_setting, building_level_int_setting, building_setting


def test_winery_building_type_loaded() -> None:
    assert building_setting("WINERY", "building_type") == "WINERY"


def test_winery_footprint() -> None:
    fp = building_setting("WINERY", "footprint")
    assert list(fp) == [2, 2]


def test_winery_input_capacity_level_1() -> None:
    cap = building_level_int_setting("WINERY", "input_storage", 1)
    assert cap == 3


def test_winery_input_capacity_level_10() -> None:
    cap = building_level_int_setting("WINERY", "input_storage", 10)
    assert cap == 12


def test_winery_output_capacity_level_1() -> None:
    cap = building_level_int_setting("WINERY", "output_storage", 1)
    assert cap == 3


def test_winery_output_capacity_level_10() -> None:
    cap = building_level_int_setting("WINERY", "output_storage", 10)
    assert cap == 12


def test_winery_recipe_input() -> None:
    recipe_in = building_setting("WINERY", "recipe", "input")
    assert recipe_in == {"grapes": 3}


def test_winery_recipe_output() -> None:
    recipe_out = building_setting("WINERY", "recipe", "output")
    assert recipe_out == {"wine": 1}


def test_winery_production_cycle_ms() -> None:
    assert building_int_setting("WINERY", "production", "cycle_ms") == 60_000


def test_winery_production_rest_ms() -> None:
    assert building_int_setting("WINERY", "production", "rest_ms") == 10_000


def test_winery_construction_level_1_cost() -> None:
    cost = building_setting("WINERY", "levels", "1", "cost")
    assert cost == {"wood": 3, "stone": 2}


def test_winery_construction_level_1_build_time() -> None:
    bt = building_int_setting("WINERY", "levels", "1", "build_time_ms")
    assert bt == 45_000
