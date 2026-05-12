"""Tests for preventing local-only elite_meal export (T377)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.resource_catalog import (
    is_local_only_meal,
    is_town_hall_warehouse_resource,
)
from game.transport_tasks import restaurant_input_transport_tasks
from game.world import World


def test_elite_meal_is_not_warehouse_resource() -> None:
    assert is_town_hall_warehouse_resource("elite_meal") is False


def test_elite_meal_is_local_only_meal() -> None:
    assert is_local_only_meal("elite_meal") is True


def test_restaurant_input_transport_rejects_elite_meal() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(10, 10))
    restaurant.construction_site = None
    tasks = restaurant_input_transport_tasks(registry, "elite_meal")
    assert tasks == []


def test_restaurant_input_transport_rejects_simple_meal() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(10, 10))
    restaurant.construction_site = None
    tasks = restaurant_input_transport_tasks(registry, "simple_meal")
    assert tasks == []


def test_no_export_function_exists_for_elite_meal() -> None:
    """There must be no restaurant output transport function that exports elite_meal."""
    import game.transport_tasks as tt
    public_names = [n for n in dir(tt) if not n.startswith("_")]
    for name in public_names:
        if "restaurant" in name.lower() and "output" in name.lower():
            raise AssertionError(f"Found output transport function: {name}")


def test_elite_meal_not_in_town_hall_warehouse_keys() -> None:
    from game.resource_catalog import TOWN_HALL_WAREHOUSE_KEYS
    assert "elite_meal" not in TOWN_HALL_WAREHOUSE_KEYS
