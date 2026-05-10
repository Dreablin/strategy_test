"""Cow Farm domain shell (T290+): type, capacity, active, processing progress; wheat slot in T291."""

from __future__ import annotations

import pytest

from game.buildings.cow_farm import CowFarm
from game.config import building_int_setting, building_level_int_setting


def test_cow_farm_type_tag_and_footprint() -> None:
    assert CowFarm.type_tag == "COW_FARM"
    assert CowFarm.footprint == (2, 2)


def test_cow_farm_storage_capacity_matches_settings() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert farm.storage_capacity() == building_level_int_setting("COW_FARM", "storage", 1)
    assert CowFarm(level=10, grid_pos=(10, 10)).storage_capacity() == building_level_int_setting(
        "COW_FARM", "storage", 10
    )


def test_cow_farm_max_level_matches_global_cap() -> None:
    CowFarm(level=10)
    with pytest.raises(ValueError):
        CowFarm(level=11)


def test_cow_farm_set_active() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert farm.active is True
    farm.set_active(False)
    assert farm.active is False


def test_cow_farm_processing_duration_loaded_from_json() -> None:
    farm = CowFarm(level=3, grid_pos=(10, 10))
    assert farm.processing_duration_ms == building_int_setting("COW_FARM", "production", "cycle_ms")


def test_cow_farm_processing_progress_and_idle_state() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert farm.processing_progress(0) == 0.0
    assert farm.progress_state(0) == "idle"
    farm.processing_started_ms = 1000
    duration = farm.processing_duration_ms
    assert farm.processing_progress(1000) == 0.0
    assert farm.progress_state(1000) == "processing"
    mid = 1000 + duration // 2
    p = farm.processing_progress(mid)
    assert 0.45 <= p <= 0.55
    end = 1000 + duration
    assert farm.processing_progress(end) == 1.0
    assert farm.progress_state(end) == "idle"
