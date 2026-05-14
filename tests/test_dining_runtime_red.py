"""RED tests for canteen dining runtime (T267); implementation in T268 (`game.worker_dining`)."""

from __future__ import annotations

from game.buildings.bakery import Bakery
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
from game.workers import WorkerManager, building_center_tile


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


def test_dining_eat_duration_is_positive() -> None:
    assert DINING_EAT_DURATION_MS > 0


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
    assert w.state == "waiting_for_meal"
    assert w.idle is False
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


def test_assigned_worker_walks_back_to_work_after_eating_instead_of_teleporting() -> None:
    world, registry, wm, c = _scene()
    bakery = registry.place(Bakery, (46, 50))
    bakery.construction_site = None
    w = Worker("BAKER", stand_tile=diner_stand_tile_for(c, Worker("BAKER")))
    w.current_tile = diner_stand_tile_for(c, w)
    w.stand_tile = w.current_tile
    w.assigned_building = bakery
    w.dining_canteen = c
    w.dining_phase = "eating"
    w.dining_eating_started_ms = 1_000
    w.state = "eating"
    w.idle = False
    c._diner_occupants.add(w)  # noqa: SLF001
    wm.add_worker(w)

    wm.update(1_000 + DINING_EAT_DURATION_MS)

    assert count_reserved_diner_slots(c) == 0
    assert dining_runtime_phase(w) == "returning_to_work"
    assert w.state == "returning"
    assert w.current_tile != building_center_tile(bakery)

    now = 1_000 + DINING_EAT_DURATION_MS
    for _ in range(300):
        now += 500
        wm.update(now)
        if dining_runtime_phase(w) == "none":
            break

    assert dining_runtime_phase(w) == "none"
    assert w.dining_canteen is None
    assert w.current_tile == building_center_tile(bakery)
    assert w.state == "working"
    assert w.idle is False


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


def test_meal_assignment_fifo_by_actual_arrival_not_reservation_order() -> None:
    world, registry, wm, c = _scene()
    c.add_local_storage("simple_meal", 1)
    reserved_first = Worker("CARRIER", stand_tile=(42, 50))
    arrived_first = Worker("CARRIER", stand_tile=(43, 50))
    assert try_reserve_diner_slot(c, reserved_first)
    assert try_reserve_diner_slot(c, arrived_first)
    reserved_first.dining_phase = "walking_to_diner"
    arrived_first.dining_phase = "waiting_for_meal"
    arrived_first.dining_queue_order = 0

    assign_diner_meals_for_canteen(c, now_ms=10_000)
    update_dining_runtime(
        reserved_first,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=10_100,
    )
    update_dining_runtime(
        arrived_first,
        canteen=c,
        world=world,
        worker_manager=wm,
        registry=registry,
        now_ms=10_100,
    )

    assert dining_runtime_phase(arrived_first) == "eating"
    assert dining_runtime_phase(reserved_first) == "walking_to_diner"
    assert c.local_storage_amount("simple_meal") == 0


def test_worker_manager_update_assigns_meal_and_runs_dining_runtime() -> None:
    _, _, wm, c = _scene()
    c.add_local_storage("simple_meal", 1)
    w = Worker("CARRIER", stand_tile=(44, 50))
    w.current_tile = w.stand_tile
    assert try_reserve_diner_slot(c, w)
    wm.add_worker(w)

    now = 0
    for _ in range(1000):
        wm.update(now)
        if dining_runtime_phase(w) == "walking_to_diner":
            assert w.state == "going_to_canteen"
            assert w.idle is False
        if dining_runtime_phase(w) == "eating":
            break
        now += 500

    assert dining_runtime_phase(w) == "eating"
    assert w.state == "eating"
    assert w.idle is False
    assert c.local_storage_amount("simple_meal") == 0
    assert dining_eating_started_ms(w) > 0


def test_cook_already_inside_own_canteen_starts_eating_without_pathing_to_itself() -> None:
    world, registry, wm, c = _scene()
    c.add_local_storage("simple_meal", 1)
    cook = Worker("COOK", stand_tile=building_center_tile(c))
    cook.current_tile = cook.stand_tile
    cook.assigned_building = c
    cook.state = "working"
    cook.idle = False
    cook.satiety = 100
    wm.add_worker(cook)

    wm.update(1_000)
    assert cook.dining_canteen is c
    assert dining_runtime_phase(cook) == "none"

    wm.update(1_500)

    assert dining_runtime_phase(cook) == "eating"
    assert cook.state == "eating"
    assert cook.current_tile == building_center_tile(c)
    assert cook.target_tile is None
    assert c.local_storage_amount("simple_meal") == 0


def test_worker_manager_update_keeps_worker_working_when_canteen_has_no_free_slot() -> None:
    world = World(world_seed=23)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, (52, 50))
    canteen.construction_site = None
    bakery = registry.place(Bakery, (46, 50))
    bakery.construction_site = None
    bakery.add_flour_in(1)
    bakery.add_water_in(1)

    wm = WorkerManager(registry)
    for i in range(canteen.diner_slot_capacity()):
        occupant = Worker("CARRIER", stand_tile=(80 + i, 80))
        assert try_reserve_diner_slot(canteen, occupant)

    baker = Worker("BAKER", stand_tile=building_center_tile(bakery))
    baker.current_tile = baker.stand_tile
    baker.assigned_building = bakery
    baker.state = "working"
    baker.idle = False
    baker.satiety = 300
    wm.add_worker(baker)

    wm.update(1_000)

    assert baker.dining_canteen is None
    assert baker.state == "processing"
    assert bakery.processing_started_ms == 1_000
