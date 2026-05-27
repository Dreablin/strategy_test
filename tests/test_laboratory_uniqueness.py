"""Laboratory uniqueness placement tests (T395)."""

from __future__ import annotations

import pytest

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World


def _registry_with_town_hall() -> BuildingRegistry:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    return registry


def test_cannot_place_second_laboratory_while_one_exists_or_under_construction() -> None:
    registry = _registry_with_town_hall()
    first_tile = near_town_hall_tile(10, 10)
    second_tile = near_town_hall_tile(22, 22)
    laboratory = registry.place(Laboratory, first_tile)
    assert laboratory.is_under_construction is True
    assert not registry.can_place(Laboratory, second_tile)
    with pytest.raises(ValueError, match="invalid placement"):
        registry.place(Laboratory, second_tile)


def test_can_place_laboratory_again_after_demolishing_existing() -> None:
    registry = _registry_with_town_hall()
    first_tile = near_town_hall_tile(10, 10)
    second_tile = near_town_hall_tile(22, 22)
    laboratory = registry.place(Laboratory, first_tile)
    registry.demolish(laboratory)
    assert registry.can_place(Laboratory, second_tile)
    replacement = registry.place(Laboratory, second_tile)
    assert replacement.type_tag == "LABORATORY"
    assert replacement.grid_pos == second_tile


def test_other_buildings_remain_placeable_when_laboratory_exists() -> None:
    registry = _registry_with_town_hall()
    registry.place(Laboratory, near_town_hall_tile(10, 10))
    winery_tile = near_town_hall_tile(22, 22)
    assert registry.can_place(Winery, winery_tile)
    winery = registry.place(Winery, winery_tile)
    assert winery.type_tag == "WINERY"
