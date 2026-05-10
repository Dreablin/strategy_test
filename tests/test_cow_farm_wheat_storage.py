"""Cow Farm wheat input slot (T291)."""

from __future__ import annotations

import pytest

from game.buildings.cow_farm import CowFarm
from game.config import building_level_int_setting


def test_cow_farm_wheat_starts_empty_and_capacity_matches_level() -> None:
    farm = CowFarm(level=4, grid_pos=(10, 10))
    cap = building_level_int_setting("COW_FARM", "storage", 4)
    assert farm.wheat_amount() == 0
    assert farm.wheat_capacity() == cap


def test_cow_farm_add_and_take_wheat() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_wheat_in(2)
    assert farm.wheat_amount() == 2
    farm.take_wheat_in(1)
    assert farm.wheat_amount() == 1


def test_cow_farm_add_wheat_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.add_wheat_in(-1)


def test_cow_farm_add_wheat_rejects_overflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    cap = farm.wheat_capacity()
    farm.add_wheat_in(cap)
    with pytest.raises(ValueError, match="overflow"):
        farm.add_wheat_in(1)


def test_cow_farm_take_wheat_rejects_negative() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        farm.take_wheat_in(-1)


def test_cow_farm_take_wheat_rejects_underflow() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.add_wheat_in(1)
    with pytest.raises(ValueError, match="insufficient"):
        farm.take_wheat_in(2)
