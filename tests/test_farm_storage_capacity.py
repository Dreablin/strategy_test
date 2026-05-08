"""RED tests for farm local storage capacity formula (T235)."""

from __future__ import annotations

from game.buildings.farm import Farm
from game.config import building_level_int_setting


def test_farm_storage_capacity_uses_building_settings() -> None:
    for level in range(1, Farm.max_level() + 1):
        farm = Farm(level=level)
        assert farm.storage_capacity() == building_level_int_setting("FARM", "storage", level)
