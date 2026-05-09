"""Phase 23 smoke: staffed WELL + WATERMAN, local water production, carriers feed two consumers."""

from __future__ import annotations

from game.buildings.bakery import Bakery
from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.worker_models import Worker
from game.workers import WorkerManager, building_center_tile


def _world() -> World:
    w = World(world_seed=23)
    w._trees.clear()  # noqa: SLF001
    w._stones.clear()  # noqa: SLF001
    return w


def test_smoke_phase23_well_waterman_production_carriers_two_consumers() -> None:
    """E2E: complete WELL construction, WATERMAN produces into storage, carriers deliver to bakery + canteen."""
    registry = BuildingRegistry(_world())
    town_hall = registry.place(TownHall, town_hall_origin_tile())

    bakery = registry.place(Bakery, near_town_hall_tile(20, 10))
    canteen = registry.place(Canteen, near_town_hall_tile(28, 10))
    bakery.construction_site = None
    canteen.construction_site = None

    well = registry.place(Well, near_town_hall_tile(12, 10))
    site = well.construction_site
    assert site is not None
    for res, amt in site.required_resources.items():
        site.deliver_resource(res, amt)
    assert site.is_fully_supplied()
    site.build_started_ms = 0

    now_ms = 0
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms)

    build_time = int(site.build_time_ms)
    now_ms = build_time + 1
    workers.update(now_ms)
    assert not well.is_under_construction
    assert well.water_amount() == 0

    well.level = 5
    waterman = Worker("WATERMAN")
    workers.add_worker(waterman)
    workers.assign_to_building(waterman, well)
    wc = building_center_tile(well)
    waterman.current_tile = wc
    waterman.stand_tile = wc
    waterman.state = "working"

    assert workers.hire("CARRIER") is not None
    assert workers.hire("CARRIER") is not None

    deadline = now_ms + 900_000
    while now_ms < deadline:
        workers.update(now_ms)
        if bakery.water_amount() >= 1 and canteen.water_amount() >= 1:
            break
        now_ms += 500

    assert bakery.water_amount() >= 1, "bakery should receive well water (second consumer not starved)"
    assert canteen.water_amount() >= 1, "canteen should receive well water"
    assert town_hall.warehouse_amount("water") == 0
