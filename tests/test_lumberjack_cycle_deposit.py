"""Failing tests for Lumberjack deposit and delivery counters (T83)."""

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _setup_single_cycle():
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    resources = None
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 3
    camp = registry.place(LumberCamp, near_town_hall_tile())
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    world._trees[(gx + 3, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(gx + 4, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    camp.level = 5
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    assert workers.hire("CARRIER") is not None
    workers.reassign_all()
    return now_ms, world, resources, camp, workers, worker, town_hall


def test_wood_added_only_on_deposit_not_on_chop_or_pickup() -> None:
    now_ms, _world, resources, _camp, workers, worker, town_hall = _setup_single_cycle()
    wh0 = town_hall.warehouse_amount("wood")

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    assert town_hall.warehouse_amount("wood") == wh0

    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    assert worker.state in {"returning", "depositing"}
    assert worker.carrying == "wood"
    assert town_hall.warehouse_amount("wood") == wh0

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "depositing"
    workers.update(now_ms[0] + 1)
    for _ in range(400):
        now_ms[0] += 1_000
        workers.update(now_ms[0])
        if town_hall.warehouse_amount("wood") >= wh0 + 1:
            break
    assert town_hall.warehouse_amount("wood") == wh0 + 1


def test_full_cycle_adds_exactly_one_wood_even_high_level_camp() -> None:
    now_ms, _world, resources, camp, workers, worker, town_hall = _setup_single_cycle()
    wh0 = town_hall.warehouse_amount("wood")
    delivered0 = camp.delivered_wood

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert worker.carrying is None
    for _ in range(400):
        now_ms[0] += 1_000
        workers.update(now_ms[0])
        if town_hall.warehouse_amount("wood") >= wh0 + 1:
            break
    assert town_hall.warehouse_amount("wood") == wh0 + 1
    assert camp.delivered_wood >= delivered0 + 1


def test_two_camps_track_deliveries_independently() -> None:
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 3
    camp_a = registry.place(LumberCamp, near_town_hall_tile())
    ax, ay = camp_a.grid_pos  # type: ignore[assignment]
    world._trees[(ax + 3, ay)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(ax + 4, ay)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    camp_b = registry.place(LumberCamp, near_town_hall_tile(18, 2))
    bx, by = camp_b.grid_pos  # type: ignore[assignment]
    world._trees[(bx + 3, by)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(bx + 4, by)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    assert workers.hire("LUMBERJACK") is not None
    assert workers.hire("LUMBERJACK") is not None
    assert workers.hire("CARRIER") is not None
    workers.reassign_all()

    wh0 = town_hall.warehouse_amount("wood")
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert camp_a.delivered_wood == 1
    assert camp_b.delivered_wood == 1
    for _ in range(600):
        now_ms[0] += 1_000
        workers.update(now_ms[0])
        if town_hall.warehouse_amount("wood") >= wh0 + 2:
            break
    assert town_hall.warehouse_amount("wood") == wh0 + 2


def test_lumberjack_does_not_start_next_cycle_when_storage_full() -> None:
    now_ms, _world, resources, camp, workers, worker, _town_hall = _setup_single_cycle()
    camp.stored = camp.storage_capacity()
    wood_before = _town_hall.warehouse_amount("wood")
    delivered_before = camp.delivered_wood

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert worker.state == "working"
    wait_until = worker.camp_wait_until_ms
    workers.update(wait_until + 500_000)
    assert worker.state == "working"
    assert worker.target_tree is None
    assert _town_hall.warehouse_amount("wood") == wood_before
    assert camp.delivered_wood == delivered_before
