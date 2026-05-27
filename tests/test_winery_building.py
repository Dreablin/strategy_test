"""Tests for Winery building class shell (T346)."""

from __future__ import annotations

import pytest

from game.buildings.winery import Winery


def test_winery_type_tag() -> None:
    w = Winery(level=1, grid_pos=(5, 5))
    assert w.type_tag == "WINERY"


def test_winery_footprint_2x2() -> None:
    assert Winery.footprint == (2, 2)


def test_winery_max_level_10() -> None:
    assert Winery.max_level() == 10


def test_winery_active_default_and_toggle() -> None:
    w = Winery(level=1, grid_pos=(5, 5))
    assert w.active is True
    w.set_active(False)
    assert w.active is False
    w.set_active(True)
    assert w.active is True


def test_winery_input_capacity_by_level() -> None:
    w1 = Winery(level=1)
    assert w1.input_capacity() > 0
    w10 = Winery(level=10)
    assert w10.input_capacity() >= w1.input_capacity()


def test_winery_output_capacity_by_level() -> None:
    w1 = Winery(level=1)
    assert w1.output_capacity() > 0
    w10 = Winery(level=10)
    assert w10.output_capacity() >= w1.output_capacity()


def test_winery_add_take_grapes() -> None:
    w = Winery(level=1)
    amount = min(2, w.input_capacity())
    w.add_grapes(amount)
    assert w.input_amount() == amount
    w.take_grapes(1)
    assert w.input_amount() == amount - 1


def test_winery_add_grapes_overflow() -> None:
    w = Winery(level=1)
    with pytest.raises(ValueError, match="overflow"):
        w.add_grapes(w.input_capacity() + 1)


def test_winery_take_grapes_insufficient() -> None:
    w = Winery(level=1)
    with pytest.raises(ValueError, match="insufficient"):
        w.take_grapes(1)


def test_winery_add_take_wine() -> None:
    w = Winery(level=1)
    w.add_wine(2)
    assert w.output_amount() == 2
    w.take_wine(1)
    assert w.output_amount() == 1


def test_winery_add_wine_overflow() -> None:
    w = Winery(level=1)
    with pytest.raises(ValueError, match="overflow"):
        w.add_wine(w.output_capacity() + 1)


def test_winery_take_wine_insufficient() -> None:
    w = Winery(level=1)
    with pytest.raises(ValueError, match="insufficient"):
        w.take_wine(1)


def test_winery_recipe_input_count() -> None:
    w = Winery(level=1)
    assert w.recipe_input_count() > 0


def test_winery_recipe_output_count() -> None:
    w = Winery(level=1)
    assert w.recipe_output_count() > 0


def test_winery_cycle_ms() -> None:
    w = Winery(level=1)
    assert w.cycle_ms() > 0


def test_winery_rest_ms() -> None:
    w = Winery(level=1)
    assert w.rest_ms() > 0


def test_winery_has_recipe_inputs() -> None:
    w = Winery(level=1)
    assert not w.has_recipe_inputs()
    w.add_grapes(w.recipe_input_count())
    assert w.has_recipe_inputs()


def test_winery_has_output_space() -> None:
    w = Winery(level=1)
    assert w.has_output_space()
    w.add_wine(w.output_capacity())
    assert not w.has_output_space()


def test_winery_processing_progress() -> None:
    w = Winery(level=1)
    assert w.processing_progress(1000) == 0.0
    w.processing_started_ms = 1000
    assert w.processing_progress(1000 + w.cycle_ms() // 2) == pytest.approx(0.5, abs=0.05)
    assert w.processing_progress(1000 + w.cycle_ms()) == 1.0


def test_winery_progress_state() -> None:
    w = Winery(level=1)
    assert w.progress_state(0) == "idle"
    w.processing_started_ms = 100
    assert w.progress_state(500) == "processing"
    assert w.progress_state(100 + w.cycle_ms()) == "idle"
