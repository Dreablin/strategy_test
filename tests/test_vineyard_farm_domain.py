"""Vineyard Farm domain shell (T314): type, grape storage, active, harvest radius from settings."""

from __future__ import annotations

import pytest

from game.buildings.vineyard_farm import VineyardFarm
from game.config import building_int_setting, building_level_int_setting


def test_vineyard_farm_type_tag_and_footprint() -> None:
    assert VineyardFarm.type_tag == "VINEYARD_FARM"
    assert VineyardFarm.footprint == (2, 2)


def test_vineyard_farm_storage_capacity_matches_settings() -> None:
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    assert farm.storage_capacity() == building_level_int_setting("VINEYARD_FARM", "storage", 1)
    assert VineyardFarm(level=10, grid_pos=(10, 10)).storage_capacity() == building_level_int_setting(
        "VINEYARD_FARM", "storage", 10
    )


def test_vineyard_farm_harvest_radius_matches_settings() -> None:
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    assert farm.harvest_radius_cells() == building_int_setting("VINEYARD_FARM", "harvest", "radius_cells")


def test_vineyard_farm_max_level_matches_global_cap() -> None:
    VineyardFarm(level=10)
    with pytest.raises(ValueError):
        VineyardFarm(level=11)


def test_vineyard_farm_set_active() -> None:
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    assert farm.active is True
    farm.set_active(False)
    assert farm.active is False


def test_vineyard_farm_grape_storage_add_and_take() -> None:
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    cap = farm.grapes_capacity()
    farm.add_grapes_to_storage(cap)
    assert farm.grapes_amount() == cap
    farm.take_grapes_from_storage(1)
    assert farm.grapes_amount() == cap - 1


def test_vineyard_farm_grape_storage_overflow() -> None:
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    cap = farm.grapes_capacity()
    farm.add_grapes_to_storage(cap)
    with pytest.raises(ValueError, match="overflow"):
        farm.add_grapes_to_storage(1)


def test_vineyard_farm_grape_storage_underflow() -> None:
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError, match="insufficient"):
        farm.take_grapes_from_storage(1)
