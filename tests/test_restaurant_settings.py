"""Tests for restaurant.json settings (T365)."""

from __future__ import annotations

from game.config import building_level_int_setting, building_setting


def test_restaurant_building_type() -> None:
    bt = building_setting("RESTAURANT", "building_type")
    assert bt == "RESTAURANT"


def test_restaurant_footprint() -> None:
    fp = building_setting("RESTAURANT", "footprint")
    assert fp == [2, 2]


def test_restaurant_storage_capacity_level_1() -> None:
    cap = building_level_int_setting("RESTAURANT", "storage", 1)
    assert cap == 3


def test_restaurant_storage_capacity_level_10() -> None:
    cap = building_level_int_setting("RESTAURANT", "storage", 10)
    assert cap == 12


def test_restaurant_diner_slots_level_1() -> None:
    slots = building_level_int_setting("RESTAURANT", "diner_slots", 1)
    assert slots == 2


def test_restaurant_diner_slots_level_10() -> None:
    slots = building_level_int_setting("RESTAURANT", "diner_slots", 10)
    assert slots == 11


def test_restaurant_recipe() -> None:
    recipe_in = building_setting("RESTAURANT", "recipe", "input")
    recipe_out = building_setting("RESTAURANT", "recipe", "output")
    assert recipe_in == {"bread": 1, "wine": 1, "beef": 1}
    assert recipe_out == {"elite_meal": 1}


def test_restaurant_production_timings() -> None:
    cycle = building_setting("RESTAURANT", "production", "cycle_ms")
    rest = building_setting("RESTAURANT", "production", "rest_ms")
    assert cycle == 45000
    assert rest == 8000


def test_restaurant_construction_level_1() -> None:
    levels = building_setting("RESTAURANT", "levels")
    assert levels["1"]["cost"] == {"boards": 5, "stone": 3, "iron": 1}
    assert levels["1"]["build_time_ms"] == 45000
