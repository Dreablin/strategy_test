"""Tests for Winery production/worker status helpers (T355)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_status import production_status_for_building
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
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return winery, workers


def test_winery_status_no_worker() -> None:
    winery, workers = _setup()
    status = production_status_for_building(workers, winery)
    assert status == "No worker"


def test_winery_status_inactive() -> None:
    winery, workers = _setup()
    winery.set_active(False)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    status = production_status_for_building(workers, winery)
    assert status == "Inactive"


def test_winery_status_no_grapes() -> None:
    winery, workers = _setup()
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winemaker.state = "working"
    status = production_status_for_building(workers, winery)
    assert status == "No grapes"


def test_winery_status_output_full() -> None:
    winery, workers = _setup()
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winery.add_grapes(winery.recipe_input_count())
    winery.add_wine(winery.output_capacity())
    winemaker.state = "working"
    status = production_status_for_building(workers, winery)
    assert status == "Output full"


def test_winery_status_processing() -> None:
    winery, workers = _setup()
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winery.add_grapes(winery.recipe_input_count())
    winemaker.state = "processing"
    status = production_status_for_building(workers, winery)
    assert status == "Processing"


def test_winery_status_resting() -> None:
    winery, workers = _setup()
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    winemaker.state = "resting"
    status = production_status_for_building(workers, winery)
    assert status == "Resting"
