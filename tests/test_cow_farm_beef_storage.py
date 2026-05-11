"""Cow Farm beef output slot (T293)."""

from __future__ import annotations

import pytest

from game.buildings.cow_farm import CowFarm
from game.config import building_level_int_setting


def test_cow_farm_beef_starts_empty_and_capacity_matches_level() -> None:
    farm = CowFarm(level=6, grid_pos=(10, 10))
    cap = building_level_int_setting("COW_FARM", "storage", 6)
    assert farm.beef_amount() == 0
    assert farm.beef_capacity() == cap


def test_cow_farm_add_and_take_beef() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_beef_out(2)
    assert farm.beef_amount() == 2
    farm.take_beef_out(1)
    assert farm.beef_amount() == 1


def test_cow_farm_add_beef_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.add_beef_out(-1)


def test_cow_farm_add_beef_rejects_overflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    cap = farm.beef_capacity()
    farm.add_beef_out(cap)
    with pytest.raises(ValueError, match="overflow"):
        farm.add_beef_out(1)


def test_cow_farm_take_beef_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.take_beef_out(-1)


def test_cow_farm_take_beef_rejects_underflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_beef_out(1)
    with pytest.raises(ValueError, match="insufficient"):
        farm.take_beef_out(2)
