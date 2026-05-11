"""Cow Farm building JSON is loaded into config (T289)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game import config


def _cow_farm_json() -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "game" / "settings" / "buildings" / "cow_farm.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_cow_farm_settings_registered_under_upper_type_tag() -> None:
    assert "COW_FARM" in config.BUILDING_SETTINGS
    assert config.building_setting("COW_FARM", "building_type") == "COW_FARM"


def test_cow_farm_storage_capacity_by_level_linear_from_three() -> None:
    assert config.building_level_int_setting("COW_FARM", "storage", 1) == 3
    assert config.building_level_int_setting("COW_FARM", "storage", 2) == 4
    assert config.building_level_int_setting("COW_FARM", "storage", 10) == 12


@pytest.mark.parametrize("level", range(1, 11))
def test_cow_farm_storage_capacity_matches_disk_json(level: int) -> None:
    raw = _cow_farm_json()["storage"]["capacity_by_level"][str(level)]
    assert config.building_level_int_setting("COW_FARM", "storage", level) == int(raw)


def test_cow_farm_production_timing_loaded_from_json() -> None:
    assert config.building_int_setting("COW_FARM", "production", "cycle_ms") == 45_000
    assert config.building_int_setting("COW_FARM", "production", "rest_ms") == 10_000


def test_cow_farm_recipe_inputs_and_outputs_match_design() -> None:
    recipe = config.building_setting("COW_FARM", "recipe")
    assert recipe["inputs"] == {"wheat": 3, "water": 3}
    assert recipe["outputs"] == {"beef": 1, "hide": 1}


def test_cow_farm_construction_levels_match_json() -> None:
    configured = _cow_farm_json()["levels"]
    loaded = config.CONSTRUCTION_REQUIREMENTS["COW_FARM"]
    assert set(loaded) == set(range(1, 11))
    for level_key, payload in configured.items():
        spec = loaded[int(level_key)]
        assert spec.cost == payload["cost"]
        assert spec.build_time_ms == payload["build_time_ms"]
