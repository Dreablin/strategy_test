"""Cow Farm water input slot (T292)."""

from __future__ import annotations

import pytest

from game.buildings.cow_farm import CowFarm
from game.config import building_level_int_setting


def test_cow_farm_water_starts_empty_and_capacity_matches_level() -> None:
    farm = CowFarm(level=5, grid_pos=(10, 10))
    cap = building_level_int_setting("COW_FARM", "storage", 5)
    assert farm.water_amount() == 0
    assert farm.water_capacity() == cap


def test_cow_farm_add_and_take_water() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_water_in(2)
    assert farm.water_amount() == 2
    farm.take_water_in(1)
    assert farm.water_amount() == 1


def test_cow_farm_add_water_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.add_water_in(-1)


def test_cow_farm_add_water_rejects_overflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    cap = farm.water_capacity()
    farm.add_water_in(cap)
    with pytest.raises(ValueError, match="overflow"):
        farm.add_water_in(1)


def test_cow_farm_take_water_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.take_water_in(-1)


def test_cow_farm_take_water_rejects_underflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_water_in(1)
    with pytest.raises(ValueError, match="insufficient"):
        farm.take_water_in(2)
