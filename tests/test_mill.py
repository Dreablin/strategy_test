"""Mill building behavior."""

from __future__ import annotations

import pytest

from game.buildings.mill import Mill
from game.config import building_level_int_setting


def test_mill_defaults_and_panel_helpers() -> None:
    mill = Mill(level=1, grid_pos=(10, 10))
    assert mill.type_tag == "MILL"
    assert mill.footprint == (2, 2)
    assert mill.active is True
    assert mill.input_amount() == 0
    assert mill.output_amount() == 0
    assert mill.input_capacity() == building_level_int_setting("MILL", "storage", 1)
    assert mill.output_capacity() == building_level_int_setting("MILL", "storage", 1)
    assert mill.progress_state(now_ms=0) == "idle"


def test_mill_split_storage_add_take_and_bounds() -> None:
    mill = Mill(level=1, grid_pos=(10, 10))
    cap = mill.input_capacity()
    mill.add_wheat_in(cap)
    mill.add_flour_out(2)
    assert mill.input_amount() == cap
    assert mill.output_amount() == 2
    mill.take_wheat_in(1)
    mill.take_flour_out(1)
    assert mill.input_amount() == cap - 1
    assert mill.output_amount() == 1
    with pytest.raises(ValueError):
        mill.add_wheat_in(2)
    with pytest.raises(ValueError):
        mill.take_flour_out(5)


def test_mill_active_toggle_and_processing_progress() -> None:
    mill = Mill(level=1, grid_pos=(10, 10))
    mill.set_active(False)
    assert mill.active is False
    mill.processing_started_ms = 1_000
    mill.processing_duration_ms = 30_000
    assert mill.progress_state(now_ms=1_000) == "processing"
    progress = mill.processing_progress(now_ms=16_000)
    assert 0.49 <= progress <= 0.51
    assert mill.processing_progress(now_ms=50_000) == 1.0


def test_mill_storage_capacity_uses_building_settings() -> None:
    for level in (1, 5, 10):
        mill = Mill(level=level, grid_pos=(10, 10))
        expected = building_level_int_setting("MILL", "storage", level)
        assert mill.input_capacity() == expected
        assert mill.output_capacity() == expected
