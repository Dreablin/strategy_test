"""Tests for Restaurant placement/construction registration (T367)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import CONSTRUCTION_REQUIREMENTS, near_town_hall_tile, town_hall_origin_tile
from game.ui.placement import PlacementController
from game.world import World


def test_restaurant_in_placement_tag_to_class() -> None:
    from game.ui.placement import _TAG_TO_CLASS

    assert "RESTAURANT" in _TAG_TO_CLASS
    assert _TAG_TO_CLASS["RESTAURANT"] is Restaurant


def test_restaurant_can_be_placed_via_registry() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(10, 10))
    assert restaurant is not None
    assert restaurant.type_tag == "RESTAURANT"
    assert restaurant.grid_pos == near_town_hall_tile(10, 10)


def test_restaurant_construction_requirements_exist() -> None:
    assert "RESTAURANT" in CONSTRUCTION_REQUIREMENTS
    specs = CONSTRUCTION_REQUIREMENTS["RESTAURANT"]
    assert 1 in specs
    assert specs[1].cost
    assert specs[1].build_time_ms > 0


def test_restaurant_placement_controller_select() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    placement = PlacementController(world, registry)
    placement.select("RESTAURANT")
    assert placement.has_pending
    assert placement.pending_type is Restaurant


def test_restaurant_starts_under_construction() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(8, 8))
    assert restaurant.is_under_construction is True
