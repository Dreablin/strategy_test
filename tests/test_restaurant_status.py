"""Tests for Restaurant production/worker status helpers (T376)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_status import production_status_for_building
from game.workers import WorkerManager
from game.world import World


def _setup():
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(5, 5))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return restaurant, workers


def test_restaurant_status_no_worker() -> None:
    restaurant, workers = _setup()
    status = production_status_for_building(workers, restaurant)
    assert status == "No worker"


def test_restaurant_status_inactive() -> None:
    restaurant, workers = _setup()
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    restaurant.set_active(False)
    status = production_status_for_building(workers, restaurant)
    assert status == "Inactive"


def test_restaurant_status_missing_inputs() -> None:
    restaurant, workers = _setup()
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    status = production_status_for_building(workers, restaurant)
    assert status == "Missing inputs"


def test_restaurant_status_output_full() -> None:
    restaurant, workers = _setup()
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    restaurant.add_local_storage("elite_meal", restaurant.output_capacity())
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)
    status = production_status_for_building(workers, restaurant)
    assert status == "Output full"


def test_restaurant_status_processing() -> None:
    restaurant, workers = _setup()
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)
    cook.state = "processing"
    status = production_status_for_building(workers, restaurant)
    assert status == "Processing"


def test_restaurant_status_resting() -> None:
    restaurant, workers = _setup()
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)
    cook.state = "resting"
    status = production_status_for_building(workers, restaurant)
    assert status == "Resting"
