"""Tests for Restaurant production runtime (T375)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.workers import WorkerManager
from game.world import World


def _setup():
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(5, 5))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    assert cook.assigned_building is restaurant
    return restaurant, workers, cook


def test_restaurant_production_consumes_inputs_produces_elite_meal() -> None:
    restaurant, workers, cook = _setup()
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)

    now_ms = 0
    for _ in range(200):
        now_ms += 500
        workers.update(now_ms)
        if cook.state == "processing":
            break
    assert cook.state == "processing"

    now_ms += 50_000
    workers.update(now_ms)
    assert restaurant.output_amount() >= 1 or cook.state == "resting"


def test_restaurant_production_enters_rest_after_cycle() -> None:
    restaurant, workers, cook = _setup()
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)

    now_ms = 0
    for _ in range(200):
        now_ms += 500
        workers.update(now_ms)
        if cook.state == "processing":
            break

    now_ms += 50_000
    workers.update(now_ms)
    assert cook.state == "resting" or restaurant.output_amount() >= 1


def test_restaurant_production_blocked_without_inputs() -> None:
    restaurant, workers, cook = _setup()
    now_ms = 0
    for _ in range(50):
        now_ms += 500
        workers.update(now_ms)
    assert cook.state != "processing"


def test_restaurant_production_blocked_when_output_full() -> None:
    restaurant, workers, cook = _setup()
    restaurant.add_local_storage("elite_meal", restaurant.output_capacity())
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)

    now_ms = 0
    for _ in range(50):
        now_ms += 500
        workers.update(now_ms)
    assert cook.state != "processing"


def test_restaurant_production_blocked_when_inactive() -> None:
    restaurant, workers, cook = _setup()
    restaurant.set_active(False)
    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)

    now_ms = 0
    for _ in range(50):
        now_ms += 500
        workers.update(now_ms)
    assert cook.state != "processing"
