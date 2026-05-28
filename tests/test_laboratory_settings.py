"""Laboratory building settings JSON tests (T392)."""

from __future__ import annotations

import json
from pathlib import Path

from game import config


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _laboratory_json() -> dict:
    path = _project_root() / "src" / "game" / "settings" / "buildings" / "laboratory.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_laboratory_settings_are_loaded_into_building_settings() -> None:
    settings = _laboratory_json()
    loaded = config.BUILDING_SETTINGS["LABORATORY"]
    assert loaded["building_type"] == settings["building_type"] == "LABORATORY"


def test_laboratory_footprint_is_loaded_from_json() -> None:
    settings = _laboratory_json()
    assert config.building_setting("LABORATORY", "footprint") == settings["footprint"]


def test_laboratory_scientist_slot_capacity_matches_json() -> None:
    by_level = _laboratory_json()["scientist_slots"]["capacity_by_level"]
    for level, expected in by_level.items():
        assert (
            config.building_level_int_setting("LABORATORY", "scientist_slots", int(level))
            == expected
        )


def test_laboratory_research_points_per_scientist_loaded_from_json() -> None:
    settings = _laboratory_json()
    expected = settings["research"]["points_per_scientist_per_second"]
    assert config.building_int_setting("LABORATORY", "research", "points_per_scientist_per_second") == expected
    assert expected > 0


def test_laboratory_technology_tier_unlock_levels_loaded_from_json() -> None:
    settings = _laboratory_json()
    unlock = settings["technology_tiers"]["unlock_level_by_tier"]
    loaded = config.building_setting("LABORATORY", "technology_tiers", "unlock_level_by_tier")
    assert loaded == unlock


def test_laboratory_construction_levels_loaded_from_json() -> None:
    settings = _laboratory_json()
    configured_levels = settings["levels"]
    loaded_levels = config.CONSTRUCTION_REQUIREMENTS["LABORATORY"]
    assert set(loaded_levels) == {int(level) for level in configured_levels}
    for level, payload in configured_levels.items():
        spec = loaded_levels[int(level)]
        assert spec.cost == payload["cost"]
        assert spec.build_time_ms == payload["build_time_ms"]


def test_laboratory_asset_defaults_and_worker_effects_loaded_from_json() -> None:
    settings = _laboratory_json()
    assert config.building_setting("LABORATORY", "asset_defaults") == settings["asset_defaults"]
    expected_level_5 = settings["worker_effects"]["by_level"]["5"]["assigned_worker"]
    assert config.building_worker_effects("LABORATORY", 5) == expected_level_5
