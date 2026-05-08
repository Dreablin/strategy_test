"""Sawmill building scaffold behavior tests (T211)."""

from __future__ import annotations

from pathlib import Path

import pytest

from game.buildings.sawmill import Sawmill
from game.config import building_level_int_setting


def test_sawmill_defaults_and_panel_helpers() -> None:
    sawmill = Sawmill(level=1, grid_pos=(10, 10))
    assert sawmill.type_tag == "SAWMILL"
    assert sawmill.footprint == (2, 2)
    assert sawmill.active is True
    assert sawmill.input_amount() == 0
    assert sawmill.output_amount() == 0
    assert sawmill.input_capacity() == building_level_int_setting("SAWMILL", "storage", 1)
    assert sawmill.output_capacity() == building_level_int_setting("SAWMILL", "storage", 1)
    assert sawmill.progress_state(now_ms=0) == "idle"


def test_sawmill_split_storage_add_take_and_bounds() -> None:
    sawmill = Sawmill(level=1, grid_pos=(10, 10))
    cap = sawmill.input_capacity()
    sawmill.add_wood_in(cap)
    sawmill.add_boards_out(2)
    assert sawmill.input_amount() == cap
    assert sawmill.output_amount() == 2
    sawmill.take_wood_in(1)
    sawmill.take_boards_out(1)
    assert sawmill.input_amount() == cap - 1
    assert sawmill.output_amount() == 1
    with pytest.raises(ValueError):
        sawmill.add_wood_in(2)
    with pytest.raises(ValueError):
        sawmill.take_boards_out(5)


def test_sawmill_active_toggle_and_processing_progress() -> None:
    sawmill = Sawmill(level=1, grid_pos=(10, 10))
    sawmill.set_active(False)
    assert sawmill.active is False
    sawmill.processing_started_ms = 1_000
    sawmill.processing_duration_ms = 30_000
    assert sawmill.progress_state(now_ms=1_000) == "processing"
    progress = sawmill.processing_progress(now_ms=16_000)
    assert 0.49 <= progress <= 0.51
    assert sawmill.processing_progress(now_ms=50_000) == 1.0


def test_sawmill_storage_capacity_uses_building_settings() -> None:
    for level in (1, 5, 10):
        sawmill = Sawmill(level=level, grid_pos=(10, 10))
        expected = building_level_int_setting("SAWMILL", "storage", level)
        assert sawmill.input_capacity() == expected
        assert sawmill.output_capacity() == expected


def test_sawmill_asset_hook_folder_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    sawmill_dir = root / "assets" / "buildings" / "sawmill"
    assert sawmill_dir.exists()
