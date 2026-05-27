"""Tests for Winery production runtime (T354)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
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
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    winemaker = workers.hire("WINEMAKER")
    assert winemaker is not None
    workers.reassign_all()
    return winery, workers, winemaker


def test_winery_production_consumes_grapes_produces_wine() -> None:
    winery, workers, winemaker = _setup()
    input_count = winery.recipe_input_count()
    output_count = winery.recipe_output_count()
    winery.add_grapes(input_count)

    now_ms = 0
    for _ in range(200):
        now_ms += 500
        workers.update(now_ms)
        if winemaker.state == "processing":
            break
    assert winemaker.state == "processing"
    assert winery.processing_started_ms > 0

    now_ms += winery.cycle_ms()
    workers.update(now_ms)
    assert winery.output_amount() == output_count
    assert winery.input_amount() == 0


def test_winery_production_enters_rest_after_cycle() -> None:
    winery, workers, winemaker = _setup()
    winery.add_grapes(winery.recipe_input_count())

    now_ms = 0
    for _ in range(200):
        now_ms += 500
        workers.update(now_ms)
        if winemaker.state == "processing":
            break

    now_ms += winery.cycle_ms()
    workers.update(now_ms)
    assert winemaker.state == "resting"
    assert winemaker.camp_wait_until_ms > 0


def test_winery_production_blocked_without_grapes() -> None:
    winery, workers, winemaker = _setup()

    now_ms = 0
    for _ in range(100):
        now_ms += 500
        workers.update(now_ms)

    assert winemaker.state != "processing"
    assert winery.processing_started_ms == 0


def test_winery_production_blocked_when_output_full() -> None:
    winery, workers, winemaker = _setup()
    winery.add_grapes(winery.recipe_input_count())
    winery.add_wine(winery.output_capacity())

    now_ms = 0
    for _ in range(100):
        now_ms += 500
        workers.update(now_ms)

    assert winemaker.state != "processing"
    assert winery.processing_started_ms == 0


def test_winery_production_blocked_when_inactive() -> None:
    winery, workers, winemaker = _setup()
    winery.add_grapes(winery.recipe_input_count())
    winery.set_active(False)

    now_ms = 0
    for _ in range(100):
        now_ms += 500
        workers.update(now_ms)

    assert winemaker.state != "processing"
