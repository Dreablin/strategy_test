"""Phase 24 smoke: Cow Farm construction, inputs, ANIMAL_HERDER cycle, beef+hide export; Town Hall never stores water."""

from __future__ import annotations

from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.worker_models import Worker
from game.workers import WorkerManager, building_center_tile


def _world() -> World:
    w = World(world_seed=24)
    w._trees.clear()  # noqa: SLF001
    w._stones.clear()  # noqa: SLF001
    w._iron.clear()  # noqa: SLF001
    w._gold.clear()  # noqa: SLF001
    return w


def _fill_well(well: Well) -> None:
    well.add_water_in(well.water_capacity())


def _place_stocked_wells(registry: BuildingRegistry, positions: list[tuple[int, int]]) -> None:
    for pos in positions:
        w = registry.place(Well, near_town_hall_tile(*pos))
        w.construction_site = None
        _fill_well(w)


def test_smoke_phase24_cow_farm_e2e_carriers_and_town_hall_exports() -> None:
    """E2E: finish Cow Farm construction, refill wheat+water via carriers, herder runs one cycle, beef+hide reach TH; TH water stays zero."""
    registry = BuildingRegistry(_world())
    th = registry.place(TownHall, town_hall_origin_tile())
    th.add_to_warehouse("wheat", 40)

    cow = registry.place(CowFarm, near_town_hall_tile(20, 8))
    site = cow.construction_site
    assert site is not None
    for res, amt in site.required_resources.items():
        site.deliver_resource(res, amt)
    assert site.is_fully_supplied()
    site.build_started_ms = 0

    _place_stocked_wells(registry, [(24, 8), (27, 8), (30, 8), (33, 8)])

    now_ms = 0
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms)
    for _ in range(6):
        assert workers.hire("CARRIER") is not None

    build_time = int(site.build_time_ms)
    now_ms = build_time + 1
    workers.update(now_ms)
    assert not cow.is_under_construction

    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, cow)
    cc = building_center_tile(cow)
    herder.current_tile = cc
    herder.stand_tile = cc
    herder.state = "working"

    deadline = now_ms + 1_200_000
    while now_ms < deadline:
        workers.update(now_ms)
        if th.warehouse_amount("beef") >= 1 and th.warehouse_amount("hide") >= 1:
            break
        now_ms += 500

    assert th.warehouse_amount("beef") >= 1, "carrier should export beef to Town Hall warehouse"
    assert th.warehouse_amount("hide") >= 1, "carrier should export hide to Town Hall warehouse"
    assert th.warehouse_amount("water") == 0
