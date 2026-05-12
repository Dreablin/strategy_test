"""Tests for Restaurant dining runtime integration (T379)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.canteen_dining import count_reserved_diner_slots
from game.canteen_selection import reserve_nearest_reachable_canteen_if_hungry
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
    restaurant.add_local_storage("elite_meal", 1)
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    assert winemaker.assigned_building is winery
    return world, registry, restaurant, winery, workers, winemaker


def test_advanced_worker_walks_to_restaurant_and_eats() -> None:
    world, registry, restaurant, winery, workers, winemaker = _setup()
    winemaker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is restaurant
    assert winemaker.dining_canteen is restaurant

    now_ms = 0
    ate = False
    for _ in range(2000):
        now_ms += 100
        workers.update(now_ms)
        if winemaker.state == "eating":
            ate = True
            break
    assert ate, f"Worker never started eating; phase={winemaker.dining_phase}, state={winemaker.state}"


def test_worker_returns_to_work_after_eating() -> None:
    world, registry, restaurant, winery, workers, winemaker = _setup()
    winemaker.satiety = 0
    reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)

    now_ms = 0
    for _ in range(5000):
        now_ms += 100
        workers.update(now_ms)
        if winemaker.dining_phase == "none" and winemaker.dining_canteen is None:
            break
    assert winemaker.dining_canteen is None
    assert winemaker.dining_phase == "none"
    assert winemaker.state in ("working", "idle")


def test_slot_released_after_eating() -> None:
    world, registry, restaurant, winery, workers, winemaker = _setup()
    winemaker.satiety = 0
    reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert count_reserved_diner_slots(restaurant) == 1

    now_ms = 0
    for _ in range(5000):
        now_ms += 100
        workers.update(now_ms)
        if winemaker.dining_canteen is None:
            break
    assert count_reserved_diner_slots(restaurant) == 0
