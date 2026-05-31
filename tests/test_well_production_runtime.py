"""Staffed well water production (T280)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import WELL_CYCLE_MS, WELL_REST_MS, Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.world import World
from game.worker_models import Worker
from game.workers import WorkerManager, building_center_tile


def _world() -> World:
    w = World(world_seed=0)
    w._trees.clear()  # noqa: SLF001
    w._stones.clear()  # noqa: SLF001
    return w


def test_well_does_not_produce_water_without_waterman() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    for now_ms in range(0, 120_000, 1_000):
        workers.update(now_ms)
    assert well.water_amount() == 0
    assert well.processing_started_ms == 0


def test_under_construction_well_does_not_start_production() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=60_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    waterman = Worker("WATERMAN")
    workers.add_worker(waterman)
    workers.assign_to_building(waterman, well)
    waterman.current_tile = building_center_tile(well)
    waterman.stand_tile = waterman.current_tile
    waterman.state = "working"

    workers.update(5_000)

    assert well.processing_started_ms == 0
    assert well.water_amount() == 0


def test_inactive_well_does_not_start_new_processing_cycle() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    well.active = False
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    waterman = Worker("WATERMAN")
    workers.add_worker(waterman)
    workers.assign_to_building(waterman, well)
    waterman.current_tile = building_center_tile(well)
    waterman.stand_tile = waterman.current_tile
    waterman.state = "working"

    workers.update(5_000)

    assert well.processing_started_ms == 0
    assert waterman.state == "resting"


def test_full_well_storage_blocks_new_production_cycles() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    well.add_water_in(well.water_capacity())
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    waterman = Worker("WATERMAN")
    workers.add_worker(waterman)
    workers.assign_to_building(waterman, well)
    waterman.current_tile = building_center_tile(well)
    waterman.stand_tile = waterman.current_tile
    waterman.state = "working"

    workers.update(50_000)

    assert well.water_amount() == well.water_capacity()
    assert well.processing_started_ms == 0


def test_waterman_adds_one_water_per_configured_cycle_and_rests() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    waterman = Worker("WATERMAN")
    workers.add_worker(waterman)
    workers.assign_to_building(waterman, well)
    waterman.current_tile = building_center_tile(well)
    waterman.stand_tile = waterman.current_tile
    waterman.state = "working"

    workers.update(1_000)
    assert waterman.state == "processing"
    assert well.processing_started_ms == 1_000

    end_cycle = 1_000 + WELL_CYCLE_MS
    workers.update(end_cycle)
    assert well.water_amount() == 1
    assert well.processing_started_ms == 0
    assert waterman.state == "resting"
    assert waterman.camp_wait_until_ms == end_cycle + WELL_REST_MS


def test_waterman_stays_at_well_center_while_processing() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    center = building_center_tile(well)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    waterman = Worker("WATERMAN")
    workers.add_worker(waterman)
    workers.assign_to_building(waterman, well)
    waterman.current_tile = center
    waterman.stand_tile = center
    waterman.state = "working"

    workers.update(3_000)
    assert waterman.current_tile == center
    assert waterman.state == "processing"


def test_production_status_matches_staffed_processor_pattern() -> None:
    registry = BuildingRegistry(_world())
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 8_000)
    waterman = Worker("WATERMAN")
    waterman.assigned_building = well
    waterman.state = "processing"
    workers.add_worker(waterman)
    well.processing_started_ms = 3_000
    well.processing_duration_ms = WELL_CYCLE_MS

    assert workers.production_status_for_building(well) == "processing"

    well.processing_started_ms = 0
    waterman.state = "resting"
    assert workers.production_status_for_building(well) == "resting"

    waterman.state = "working"
    well.add_water_in(well.water_capacity())
    assert workers.production_status_for_building(well) == "output_full"
