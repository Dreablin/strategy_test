"""RED tests for post-cycle hunger → canteen attempt (T269); implementation in T270 (`game.worker_hunger`)."""

from __future__ import annotations

import pytest

from game.buildings.bakery import Bakery
from game.buildings.canteen import Canteen
from game.buildings.farm import Farm
from game.buildings.field import Field
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.canteen_dining import try_reserve_diner_slot
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.iron import IronDeposit
from game.worker_hunger import try_hunger_canteen_after_completed_cycle
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager


def _base() -> tuple[World, BuildingRegistry, WorkerManager, Canteen]:
    world = World(world_seed=31)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    for b in registry.all():
        if b.type_tag == "TOWN_HALL":
            b.level = 5
            break
    canteen = registry.place(Canteen, (52, 50))
    canteen.construction_site = None
    wm = WorkerManager(registry)
    return world, registry, wm, canteen


def _post_cycle_resting_worker(w: Worker, *, now_ms: int = 10_000) -> None:
    w.state = "resting"
    w.idle = False
    w.camp_wait_until_ms = int(now_ms) + 8_000


def _place_iron_mine(registry: BuildingRegistry) -> object:
    world = registry._world  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    mine_pos = near_town_hall_tile(12, 4)
    world._iron[mine_pos] = IronDeposit(blocking=False)  # noqa: SLF001
    return registry.place(IronMine, mine_pos)


@pytest.mark.parametrize(
    "type_tag, place_building",
    [
        ("BAKER", lambda r: r.place(Bakery, near_town_hall_tile(6, 4))),
        ("LUMBERJACK", lambda r: r.place(LumberCamp, near_town_hall_tile(4, 6))),
        ("MINER", _place_iron_mine),
        ("FARMER", lambda r: r.place(Farm, near_town_hall_tile(8, 4))),
    ],
)
def test_hungry_worker_attempts_canteen_after_cycle_per_family(
    type_tag: str,
    place_building,
) -> None:
    world, registry, wm, canteen = _base()
    b = place_building(registry)
    b.construction_site = None
    if type_tag == "FARMER":
        registry.place(Field, near_town_hall_tile(10, 10)).construction_site = None
    worker = Worker(type_tag, stand_tile=(46, 50))
    worker.current_tile = worker.stand_tile
    worker.assigned_building = b
    worker.satiety = 500
    _post_cycle_resting_worker(worker, now_ms=20_000)
    assert try_hunger_canteen_after_completed_cycle(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=20_000,
    )
    assert worker.dining_canteen is canteen


def test_when_no_canteen_hunger_does_not_reserve_rest_unchanged() -> None:
    world = World(world_seed=32)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(6, 4))
    bakery.construction_site = None
    wm = WorkerManager(registry)
    worker = Worker("BAKER", stand_tile=(46, 50))
    worker.current_tile = worker.stand_tile
    worker.assigned_building = bakery
    worker.satiety = 400
    _post_cycle_resting_worker(worker, now_ms=15_000)
    before_wait = worker.camp_wait_until_ms
    assert not try_hunger_canteen_after_completed_cycle(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=15_000,
    )
    assert worker.dining_canteen is None
    assert worker.state == "resting"
    assert worker.camp_wait_until_ms == before_wait


def test_when_all_diner_slots_full_hunger_does_not_reserve_rest_unchanged() -> None:
    world, registry, wm, canteen = _base()
    bakery = registry.place(Bakery, near_town_hall_tile(6, 4))
    bakery.construction_site = None
    for i in range(canteen.diner_slot_capacity()):
        w = Worker("CARRIER", stand_tile=(80 + i, 80))
        assert try_reserve_diner_slot(canteen, w)
    worker = Worker("BAKER", stand_tile=(46, 50))
    worker.current_tile = worker.stand_tile
    worker.assigned_building = bakery
    worker.satiety = 300
    _post_cycle_resting_worker(worker, now_ms=12_000)
    before_wait = worker.camp_wait_until_ms
    assert not try_hunger_canteen_after_completed_cycle(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=12_000,
    )
    assert worker.dining_canteen is None
    assert worker.state == "resting"
    assert worker.camp_wait_until_ms == before_wait


def test_not_hungry_skips_canteen_attempt() -> None:
    world, registry, wm, _ = _base()
    bakery = registry.place(Bakery, near_town_hall_tile(6, 4))
    bakery.construction_site = None
    worker = Worker("BAKER", stand_tile=(46, 50))
    worker.current_tile = worker.stand_tile
    worker.assigned_building = bakery
    worker.satiety = 5_000
    _post_cycle_resting_worker(worker, now_ms=9_000)
    assert not try_hunger_canteen_after_completed_cycle(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=9_000,
    )
    assert worker.dining_canteen is None
