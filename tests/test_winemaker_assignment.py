"""Tests for Winemaker-to-Winery compatibility and assignment (T353)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hiring import WORKER_TO_BUILDING, worker_compatible_building_types
from game.workers import WorkerManager
from game.world import World


def test_winemaker_maps_to_winery_in_worker_to_building() -> None:
    assert WORKER_TO_BUILDING["WINEMAKER"] == "WINERY"


def test_winemaker_compatible_with_winery() -> None:
    compatible = worker_compatible_building_types("WINEMAKER")
    assert "WINERY" in compatible


def test_winemaker_not_compatible_with_other_buildings() -> None:
    compatible = worker_compatible_building_types("WINEMAKER")
    assert "BAKERY" not in compatible
    assert "FARM" not in compatible
    assert "MILL" not in compatible


def test_winemaker_auto_assigned_to_built_winery() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None

    workers.reassign_all()
    assert winemaker.assigned_building is winery


def test_other_workers_not_assigned_to_winery() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    workers.reassign_all()
    assert carrier.assigned_building is not winery
