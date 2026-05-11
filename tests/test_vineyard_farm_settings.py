"""Vineyard Farm building JSON is loaded into config (T313)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game import config


def _vineyard_farm_json() -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "game" / "settings" / "buildings" / "vineyard_farm.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_vineyard_farm_settings_registered_under_upper_type_tag() -> None:
    assert "VINEYARD_FARM" in config.BUILDING_SETTINGS
    assert config.building_setting("VINEYARD_FARM", "building_type") == "VINEYARD_FARM"


def test_vineyard_farm_harvest_radius_loaded_from_json() -> None:
    assert config.building_int_setting("VINEYARD_FARM", "harvest", "radius_cells") == 15


def test_vineyard_farm_grape_storage_capacity_by_level_linear_from_three() -> None:
    assert config.building_level_int_setting("VINEYARD_FARM", "storage", 1) == 3
    assert config.building_level_int_setting("VINEYARD_FARM", "storage", 2) == 4
    assert config.building_level_int_setting("VINEYARD_FARM", "storage", 10) == 12


@pytest.mark.parametrize("level", range(1, 11))
def test_vineyard_farm_storage_capacity_matches_disk_json(level: int) -> None:
    raw = _vineyard_farm_json()["storage"]["capacity_by_level"][str(level)]
    assert config.building_level_int_setting("VINEYARD_FARM", "storage", level) == int(raw)


def test_vineyard_farm_worker_effects_match_farm_style_per_level() -> None:
    farm = config.building_setting("FARM", "worker_effects")
    vineyard = config.building_setting("VINEYARD_FARM", "worker_effects")
    assert vineyard == farm


def test_vineyard_farm_construction_levels_match_json() -> None:
    configured = _vineyard_farm_json()["levels"]
    loaded = config.CONSTRUCTION_REQUIREMENTS["VINEYARD_FARM"]
    assert set(loaded) == set(range(1, 11))
    for level_key, payload in configured.items():
        spec = loaded[int(level_key)]
        assert spec.cost == payload["cost"]
        assert spec.build_time_ms == payload["build_time_ms"]
