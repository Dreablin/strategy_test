"""Tests for Restaurant wine input transport (T373)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import restaurant_input_transport_tasks
from game.world import World


def _setup():
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(10, 10))
    restaurant.construction_site = None
    return world, registry, town_hall, restaurant


def test_wine_tasks_generated_for_free_capacity() -> None:
    world, registry, town_hall, restaurant = _setup()
    town_hall.add_to_warehouse("wine", restaurant.local_storage_capacity("wine"))
    tasks = restaurant_input_transport_tasks(registry, "wine")
    assert len(tasks) == restaurant.local_storage_capacity("wine")
    assert all(t.resource == "wine" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is restaurant for t in tasks)


def test_wine_tasks_limited_by_warehouse_stock() -> None:
    world, registry, town_hall, restaurant = _setup()
    town_hall.add_to_warehouse("wine", 1)
    tasks = restaurant_input_transport_tasks(registry, "wine")
    assert len(tasks) == 1


def test_wine_tasks_empty_when_no_stock() -> None:
    world, registry, town_hall, restaurant = _setup()
    tasks = restaurant_input_transport_tasks(registry, "wine")
    assert tasks == []


def test_wine_tasks_skip_full_restaurant() -> None:
    world, registry, town_hall, restaurant = _setup()
    town_hall.add_to_warehouse("wine", restaurant.local_storage_capacity("wine"))
    restaurant.add_local_storage("wine", restaurant.local_storage_capacity("wine"))
    tasks = restaurant_input_transport_tasks(registry, "wine")
    assert tasks == []


def test_wine_tasks_skip_inactive() -> None:
    world, registry, town_hall, restaurant = _setup()
    town_hall.add_to_warehouse("wine", 5)
    restaurant.set_active(False)
    tasks = restaurant_input_transport_tasks(registry, "wine")
    assert tasks == []
