"""Tests for Restaurant dining selection for advanced workers (T378)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.canteen_selection import reserve_nearest_reachable_canteen_if_hungry
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_tiers import worker_tier
from game.workers import WorkerManager
from game.world import World


def _setup_both():
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(5, 5))
    canteen.construction_site = None
    canteen.add_local_storage("simple_meal", 2)
    restaurant = registry.place(Restaurant, near_town_hall_tile(8, 8))
    restaurant.construction_site = None
    restaurant.add_local_storage("elite_meal", 2)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return world, registry, canteen, restaurant, workers


def test_advanced_worker_reserves_restaurant() -> None:
    world, registry, canteen, restaurant, workers = _setup_both()
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    assert worker_tier("WINEMAKER") == "advanced"
    winemaker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is restaurant


def test_basic_worker_reserves_canteen_not_restaurant() -> None:
    world, registry, canteen, restaurant, workers = _setup_both()
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    assert worker_tier("BAKER") == "basic"
    baker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, baker)
    assert result is canteen


def test_advanced_worker_no_reservation_without_elite_meal() -> None:
    world, registry, canteen, restaurant, workers = _setup_both()
    restaurant.take_local_storage("elite_meal", 2)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winemaker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is None


def test_worker_does_not_leave_when_no_meal_available() -> None:
    """Advanced worker keeps working if restaurant has free slots but no elite_meal."""
    world, registry, canteen, restaurant, workers = _setup_both()
    restaurant.take_local_storage("elite_meal", 2)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winemaker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is None
    assert winemaker.dining_canteen is None
