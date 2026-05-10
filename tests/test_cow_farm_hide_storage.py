"""Cow Farm hide output slot (T294)."""

from __future__ import annotations

import pytest

from game.buildings.cow_farm import CowFarm
from game.config import building_level_int_setting


def test_cow_farm_hide_starts_empty_and_capacity_matches_level() -> None:
    farm = CowFarm(level=7, grid_pos=(10, 10))
    cap = building_level_int_setting("COW_FARM", "storage", 7)
    assert farm.hide_amount() == 0
    assert farm.hide_capacity() == cap


def test_cow_farm_add_and_take_hide() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_hide_out(2)
    assert farm.hide_amount() == 2
    farm.take_hide_out(1)
    assert farm.hide_amount() == 1


def test_cow_farm_add_hide_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.add_hide_out(-1)


def test_cow_farm_add_hide_rejects_overflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    cap = farm.hide_capacity()
    farm.add_hide_out(cap)
    with pytest.raises(ValueError, match="overflow"):
        farm.add_hide_out(1)


def test_cow_farm_take_hide_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.take_hide_out(-1)


def test_cow_farm_take_hide_rejects_underflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_hide_out(1)
    with pytest.raises(ValueError, match="insufficient"):
        farm.take_hide_out(2)
