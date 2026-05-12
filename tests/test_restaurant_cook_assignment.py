"""Tests for Cook-to-Restaurant compatibility and assignment (T371)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hiring import worker_compatible_building_types
from game.workers import WorkerManager
from game.world import World


def test_cook_compatible_with_canteen() -> None:
    types = worker_compatible_building_types("COOK")
    assert "CANTEEN" in types


def test_cook_compatible_with_restaurant() -> None:
    types = worker_compatible_building_types("COOK")
    assert "RESTAURANT" in types


def test_cook_not_compatible_with_other_buildings() -> None:
    types = worker_compatible_building_types("COOK")
    assert "BAKERY" not in types
    assert "WINERY" not in types


def test_cook_auto_assigned_to_built_canteen() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(5, 5))
    canteen.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    assert cook.assigned_building is canteen


def test_cook_auto_assigned_to_built_restaurant() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(5, 5))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    assert cook.assigned_building is restaurant


def test_cook_prefers_canteen_when_both_available() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(5, 5))
    canteen.construction_site = None
    restaurant = registry.place(Restaurant, near_town_hall_tile(8, 8))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    assert cook.assigned_building in (canteen, restaurant)


def test_other_workers_not_assigned_to_restaurant() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(5, 5))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    assert baker.assigned_building is not restaurant
