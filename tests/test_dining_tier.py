"""Tests for dining tier metadata (T364)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.canteen_selection import reserve_nearest_reachable_canteen_if_hungry
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_tiers import worker_tier
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
    canteen.add_local_storage("simple_meal", 2)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return world, registry, canteen, workers


def test_canteen_dining_tier_is_basic() -> None:
    c = Canteen(level=1)
    assert c.dining_tier() == "basic"


def test_basic_worker_can_reserve_canteen_meal() -> None:
    world, registry, canteen, workers = _setup()
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    assert worker_tier("BAKER") == "basic"
    baker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, baker)
    assert result is canteen


def test_advanced_worker_cannot_reserve_canteen_meal() -> None:
    world, registry, canteen, workers = _setup()
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    assert worker_tier("WINEMAKER") == "advanced"
    winemaker.satiety = 0
    result = reserve_nearest_reachable_canteen_if_hungry(world, registry, workers, winemaker)
    assert result is None
