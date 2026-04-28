"""Failing tests for House domain/placement behavior (T167)."""

from __future__ import annotations

import pytest

from game.buildings.house import House
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.housing import max_population
from game.world import World


def test_house_type_footprint_and_levels() -> None:
    assert House.type_tag == "HOUSE"
    assert House.footprint == (2, 2)
    assert House.max_level() == 10


def test_house_contributes_housing_by_level_formula() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 1
    house = registry.place(House, near_town_hall_tile(8, 8))
    house.level = 4  # 2 + 2*(4-1) = 8
    assert max_population(registry, 0) == 16  # TH level1 -> 8; house level4 -> 8


def test_registry_places_house_and_blocks_overlap() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    pos = near_town_hall_tile(8, 8)
    house = registry.place(House, pos)
    assert house.type_tag == "HOUSE"
    assert not registry.can_place(House, pos)
    with pytest.raises(ValueError):
        registry.place(House, pos)
