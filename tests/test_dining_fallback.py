"""Tests for dining fallback behavior (T380)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
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
    canteen = registry.place(Canteen, near_town_hall_tile(5, 5))
    canteen.construction_site = None
    restaurant = registry.place(Restaurant, near_town_hall_tile(8, 8))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return world, registry, canteen, restaurant, workers


def test_hungry_advanced_worker_keeps_working_no_restaurant_meal() -> None:
    """Advanced worker stays working when no elite_meal is available."""
    world, registry, canteen, restaurant, workers = _setup()
    canteen.add_local_storage("simple_meal", 3)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winemaker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is None
    assert winemaker.dining_canteen is None


def test_hungry_basic_worker_keeps_working_only_restaurant_meals() -> None:
    """Basic worker keeps working when only Restaurant meals exist (can't use Restaurant)."""
    world, registry, canteen, restaurant, workers = _setup()
    restaurant.add_local_storage("elite_meal", 3)
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    baker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, baker)
    assert result is None
    assert baker.dining_canteen is None


def test_reserved_meals_prevent_over_assignment() -> None:
    """When multiple hungry workers compete for fewer meals, only available meals are reserved."""
    world, registry, canteen, restaurant, workers = _setup()
    restaurant.add_local_storage("elite_meal", 1)
    winemaker1 = workers.hire("WINEMAKER")
    winemaker2 = workers.hire("WINEMAKER")
    assert winemaker1 is not None
    assert winemaker2 is not None
    workers.reassign_all()
    winemaker1.satiety = 0
    winemaker2.satiety = 0

    r1 = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker1)
    r2 = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker2)
    reserved_count = sum(1 for r in [r1, r2] if r is not None)
    assert reserved_count == 1
