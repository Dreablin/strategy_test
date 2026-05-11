"""Cow Farm recipe and production helpers from JSON (T295)."""

from __future__ import annotations

import json
from pathlib import Path

from game.buildings.cow_farm import CowFarm
from game.config import building_int_setting


def _cow_json() -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "game" / "settings" / "buildings" / "cow_farm.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_cow_farm_recipe_amounts_match_json_file() -> None:
    raw = _cow_json()["recipe"]
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert farm.recipe_wheat_required() == int(raw["inputs"]["wheat"])
    assert farm.recipe_water_required() == int(raw["inputs"]["water"])
    assert farm.recipe_beef_output() == int(raw["outputs"]["beef"])
    assert farm.recipe_hide_output() == int(raw["outputs"]["hide"])


def test_cow_farm_production_rest_ms_matches_json() -> None:
    expected = building_int_setting("COW_FARM", "production", "rest_ms")
    assert CowFarm(level=1, grid_pos=(10, 10)).production_rest_ms() == int(expected)


def test_cow_farm_has_recipe_inputs() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert farm.has_recipe_inputs() is False
    farm.add_wheat_in(3)
    assert farm.has_recipe_inputs() is False
    farm.add_water_in(3)
    assert farm.has_recipe_inputs() is True
    farm.take_wheat_in(1)
    assert farm.has_recipe_inputs() is False


def test_cow_farm_has_recipe_output_space() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert farm.has_recipe_output_space() is True
    cap = farm.beef_capacity()
    farm.add_beef_out(cap)
    assert farm.has_recipe_output_space() is False
    farm.take_beef_out(cap)
    farm.add_hide_out(cap)
    assert farm.has_recipe_output_space() is False


def test_cow_farm_processing_progress_and_state_use_cycle_duration_from_settings() -> None:
    farm = CowFarm(level=2, grid_pos=(10, 10))
    duration = building_int_setting("COW_FARM", "production", "cycle_ms")
    assert farm.processing_duration_ms == int(duration)
    farm.processing_started_ms = 5000
    assert farm.processing_progress(5000) == 0.0
    assert farm.progress_state(5000) == "processing"
    assert farm.processing_progress(5000 + int(duration)) == 1.0
    assert farm.progress_state(5000 + int(duration)) == "idle"
