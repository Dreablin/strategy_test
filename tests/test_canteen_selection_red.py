"""RED tests for hungry-worker canteen selection (T265); implementation in T266 (`game.canteen_selection`)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.canteen_dining import count_reserved_diner_slots, try_reserve_diner_slot
from game.canteen_selection import (
    HUNGER_SATIETY_THRESHOLD,
    reserve_nearest_reachable_canteen_if_hungry,
)
from game.config import town_hall_origin_tile
from game.construction import ConstructionSite
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager


def _base_world() -> tuple[World, BuildingRegistry, WorkerManager]:
    world = World(world_seed=11)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    return world, registry, wm


def test_not_hungry_does_not_reserve() -> None:
    world, registry, wm = _base_world()
    registry.place(Canteen, (48, 48)).construction_site = None
    worker = Worker("FARMER", stand_tile=(46, 48))
    worker.satiety = HUNGER_SATIETY_THRESHOLD
    worker.state = "idle"
    assert reserve_nearest_reachable_canteen_if_hungry(world=world, registry=registry, worker_manager=wm, worker=worker) is None
    assert worker.dining_canteen is None


def test_hungry_reserves_without_simple_meal_in_canteen() -> None:
    world, registry, wm = _base_world()
    c = registry.place(Canteen, (50, 48))
    c.construction_site = None
    assert c.local_storage_amount("simple_meal") == 0
    worker = Worker("LUMBERJACK", stand_tile=(46, 48))
    worker.satiety = HUNGER_SATIETY_THRESHOLD - 1
    chosen = reserve_nearest_reachable_canteen_if_hungry(
        world=world, registry=registry, worker_manager=wm, worker=worker
    )
    assert chosen is c
    assert worker.dining_canteen is c
    assert count_reserved_diner_slots(c) == 1


def test_hungry_picks_nearest_reachable_canteen() -> None:
    world, registry, wm = _base_world()
    far = registry.place(Canteen, (58, 48))
    far.construction_site = None
    near = registry.place(Canteen, (52, 48))
    near.construction_site = None
    worker = Worker("MINER", stand_tile=(46, 48))
    worker.satiety = 500
    chosen = reserve_nearest_reachable_canteen_if_hungry(
        world=world, registry=registry, worker_manager=wm, worker=worker
    )
    assert chosen is near
    assert worker.dining_canteen is near


def test_hungry_skips_full_canteen_for_next_with_free_slot() -> None:
    world, registry, wm = _base_world()
    near = registry.place(Canteen, (52, 48))
    near.construction_site = None
    far = registry.place(Canteen, (58, 48))
    far.construction_site = None
    for w in (Worker("CARRIER", stand_tile=(60 + i, 60)) for i in range(near.diner_slot_capacity())):
        assert try_reserve_diner_slot(near, w) is True
    worker = Worker("BAKER", stand_tile=(46, 48))
    worker.satiety = 100
    chosen = reserve_nearest_reachable_canteen_if_hungry(
        world=world, registry=registry, worker_manager=wm, worker=worker
    )
    assert chosen is far
    assert worker.dining_canteen is far


def test_skips_canteen_under_construction() -> None:
    world, registry, wm = _base_world()
    bad = registry.place(Canteen, (52, 48))
    bad.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=1000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    good = registry.place(Canteen, (58, 48))
    good.construction_site = None
    worker = Worker("SAWYER", stand_tile=(46, 48))
    worker.satiety = 100
    chosen = reserve_nearest_reachable_canteen_if_hungry(
        world=world, registry=registry, worker_manager=wm, worker=worker
    )
    assert chosen is good


def test_no_reservation_when_all_slots_full_worker_keeps_working_state() -> None:
    world, registry, wm = _base_world()
    a = registry.place(Canteen, (52, 48))
    a.construction_site = None
    b = registry.place(Canteen, (58, 48))
    b.construction_site = None
    fillers: list[Worker] = []
    for c in (a, b):
        for _ in range(c.diner_slot_capacity()):
            w = Worker("CARRIER", stand_tile=(70 + len(fillers), 70))
            assert try_reserve_diner_slot(c, w) is True
            fillers.append(w)
    worker = Worker("MILLER", stand_tile=(46, 48))
    worker.satiety = 100
    worker.state = "working"
    worker.idle = False
    assert (
        reserve_nearest_reachable_canteen_if_hungry(
            world=world, registry=registry, worker_manager=wm, worker=worker
        )
        is None
    )
    assert worker.dining_canteen is None
    assert worker.state == "working"
    assert worker.idle is False
