"""RED tests for canteen dining runtime (T267); implementation in T268 (`game.worker_dining`)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.canteen_dining import count_reserved_diner_slots, try_reserve_diner_slot
from game.config import town_hall_origin_tile
from game.worker_dining import (
    DINING_EAT_DURATION_MS,
    assign_diner_meals_for_canteen,
    diner_stand_tile_for,
    dining_eating_started_ms,
    dining_runtime_phase,
    update_dining_runtime,
)
from game.worker_models import Worker
from game.worker_satiety import MAX_WORKER_SATIETY
from game.world import World
from game.workers import WorkerManager


def _scene() -> tuple[World, BuildingRegistry, WorkerManager, Canteen]:
    world = World(world_seed=21)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, (52, 50))
    canteen.construction_site = None
    wm = WorkerManager(registry)
    return world, registry, wm, canteen


def test_dining_eat_duration_is_twenty_seconds() -> None:
    assert DINING_EAT_DURATION_MS == 20_000


def test_diner_stand_tile_is_deterministic_per_worker() -> None:
    _, _, _, c = _scene()
    a = Worker("FARMER", stand_tile=(40, 50))
    b = Worker("MINER", stand_tile=(41, 50))
    try_reserve_diner_slot(c, a)
    try_reserve_diner_slot(c, b)
    ta = diner_stand_tile_for(c, a)
    tb = diner_stand_tile_for(c, b)
    assert ta == diner_stand_tile_for(c, a)
    assert tb == diner_stand_tile_for(c, b)
    assert ta != tb


def test_reserved_worker_reaches_stand_tile_via_runtime_ticks() -> None:
    world, registry, wm, c = _scene()
    w = Worker("LUMBERJACK", stand_tile=(44, 50))
    w.current_tile = w.stand_tile
    assert try_reserve_diner_slot(c, w)
    target = diner_stand_tile_for(c, w)
    assert w.current_tile != target
    now = 0
    for _ in range(500):
        update_dining_runtime(
            w,
            canteen=c,
            world=world,
            worker_manager=wm,
            registry=registry,
            now_ms=now,
        )
        if w.current_tile == target:
            break
        now += 400
    assert w.current_tile == target


def test_waiting_worker_does_not_start_eating_without_meal() -> None:
    world, registry, wm, c = _scene()
    assert c.local_storage_amount("simple_meal") == 0
    w = Worker("BAKER", stand_tile=(44, 50))
    w.current_tile = w.stand_tile
    assert try_reserve_diner_slot(c, w)
    target = diner_stand_tile_for(c, w)
    now = 0
    while w.current_tile != target and now < 600_000:
        update_dining_runtime(
            w,
            canteen=c,
            world=world,
            worker_manager=wm,
            registry=registry,
            now_ms=now,
        )
        now += 500
    assert w.current_tile == target
    update_dining_runtime(
        w,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=now + 5_000,
    )
    assert dining_runtime_phase(w) == "waiting_for_meal"
    assert dining_eating_started_ms(w) == 0


def test_eating_starts_only_after_meal_assigned_and_consumes_one_meal() -> None:
    world, registry, wm, c = _scene()
    c.add_local_storage("simple_meal", 1)
    w = Worker("SAWYER", stand_tile=(44, 50))
    w.current_tile = w.stand_tile
    assert try_reserve_diner_slot(c, w)
    target = diner_stand_tile_for(c, w)
    now = 0
    while w.current_tile != target and now < 600_000:
        update_dining_runtime(
            w,
            canteen=c,
            world=world,
            worker_manager=wm,
            registry=registry,
            now_ms=now,
        )
        now += 500
    assign_diner_meals_for_canteen(c, now_ms=now)
    update_dining_runtime(
        w,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=now + 100,
    )
    assert dining_runtime_phase(w) == "eating"
    assert dining_eating_started_ms(w) > 0
    assert c.local_storage_amount("simple_meal") == 0


def test_after_eating_duration_satiety_max_slot_released_idle() -> None:
    world, registry, wm, c = _scene()
    c.add_local_storage("simple_meal", 1)
    w = Worker("MILLER", stand_tile=(44, 50))
    w.current_tile = w.stand_tile
    w.satiety = 500
    assert try_reserve_diner_slot(c, w)
    target = diner_stand_tile_for(c, w)
    now = 0
    while w.current_tile != target and now < 600_000:
        update_dining_runtime(
            w,
            canteen=c,
            world=world,
            worker_manager=wm,
            registry=registry,
            now_ms=now,
        )
        now += 500
    assign_diner_meals_for_canteen(c, now_ms=now)
    update_dining_runtime(
        w,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=now + 50,
    )
    started = dining_eating_started_ms(w)
    assert started > 0
    end_ms = started + DINING_EAT_DURATION_MS + 50
    update_dining_runtime(
        w,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=end_ms,
    )
    assert w.satiety == MAX_WORKER_SATIETY
    assert w.dining_canteen is None
    assert count_reserved_diner_slots(c) == 0
    assert dining_runtime_phase(w) == "none"
    assert w.state == "idle"
    assert w.idle is True


def test_deterministic_single_meal_to_one_waiting_worker() -> None:
    world, registry, wm, c = _scene()
    c.add_local_storage("simple_meal", 1)
    w1 = Worker("CARRIER", stand_tile=(42, 50))
    w2 = Worker("CARRIER", stand_tile=(43, 50))
    w1.current_tile = w1.stand_tile
    w2.current_tile = w2.stand_tile
    assert try_reserve_diner_slot(c, w1)
    assert try_reserve_diner_slot(c, w2)
    for w in (w1, w2):
        target = diner_stand_tile_for(c, w)
        now = 0
        while w.current_tile != target and now < 600_000:
            update_dining_runtime(
                w,
                canteen=c,
                world=world,
                worker_manager=wm,
                registry=registry,
                now_ms=now,
            )
            now += 500
    assign_diner_meals_for_canteen(c, now_ms=10_000)
    update_dining_runtime(
        w1,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=10_100,
    )
    update_dining_runtime(
        w2,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=10_100,
    )
    eating = sum(1 for w in (w1, w2) if dining_runtime_phase(w) == "eating")
    waiting = sum(1 for w in (w1, w2) if dining_runtime_phase(w) == "waiting_for_meal")
    assert eating == 1
    assert waiting == 1
