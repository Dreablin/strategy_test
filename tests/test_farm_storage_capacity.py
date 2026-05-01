"""RED tests for farm local storage capacity formula (T235)."""

from __future__ import annotations

from game.buildings.farm import Farm


def test_farm_storage_capacity_grows_by_one_every_two_levels() -> None:
    expected = {
        1: 3,
        2: 3,
        3: 4,
        4: 4,
        5: 5,
        6: 5,
        7: 6,
        8: 6,
        9: 7,
        10: 7,
    }
    for level, capacity in expected.items():
        farm = Farm(level=level)
        assert farm.storage_capacity() == capacity
