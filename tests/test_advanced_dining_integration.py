"""Focused advanced dining integration test (T385).

Covers the full lifecycle for an advanced worker:
  1. Worker becomes hungry (satiety drops to 0).
  2. Reserves a Restaurant meal and diner slot.
  3. Walks to the Restaurant (not teleporting).
  4. Eats elite_meal, restoring satiety.
  5. Diner slot is released.
  6. Returns to work without teleporting.
"""

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


def test_advanced_dining_full_lifecycle() -> None:
    world, registry, restaurant, winery, workers, winemaker = _setup()

    winemaker.satiety = 0

    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is restaurant, "Expected Restaurant reservation"
    assert winemaker.dining_canteen is restaurant
    assert winemaker.dining_meal_reserved is True
    assert count_reserved_diner_slots(restaurant) == 1

    start_tile = winemaker.current_tile

    now_ms = 0
    walked = False
    for _ in range(2000):
        now_ms += 100
        workers.update(now_ms)
        if winemaker.current_tile != start_tile:
            walked = True
        if winemaker.state == "eating":
            break
    assert walked, "Worker should walk toward Restaurant, not teleport"
    assert winemaker.state == "eating", (
        f"Worker should be eating; state={winemaker.state}, phase={winemaker.dining_phase}"
    )

    for _ in range(3000):
        now_ms += 100
        workers.update(now_ms)
        if winemaker.dining_phase == "none" and winemaker.dining_canteen is None:
            break
    assert winemaker.dining_canteen is None, "Dining should have ended"
    assert winemaker.dining_phase == "none"
    assert count_reserved_diner_slots(restaurant) == 0, "Diner slot should be released"

    assert winemaker.satiety > 0, "Satiety should be restored after eating"

    assert winemaker.state in ("working", "idle"), (
        f"Worker should have returned to work; state={winemaker.state}"
    )
