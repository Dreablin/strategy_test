"""Failing tests for Lumber Camp Active toggle behavior (T85)."""

import pytest

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _setup_toggle_world():
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    resources = None
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 3
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camp.construction_site = None
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    world._trees[(gx + 3, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(gx + 4, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    return now_ms, world, resources, registry, camp, workers, worker


def _advance_to_chopping(now_ms, workers, worker) -> None:
    workers.reassign_all()
    # Worker first enters camp, waits, then exits to chop.
    for _ in range(120):
        if worker.state == "chopping":
            break
        now_ms[0] += 3_000
        workers.update(now_ms[0])
    else:
        pytest.fail(f"worker did not reach chopping, current state={worker.state!r}")
    assert worker.state == "chopping"


def _complete_one_cycle(now_ms, workers) -> None:
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)


def test_toggle_off_before_assignment_keeps_worker_idle_and_no_delivery() -> None:
    _now_ms, _world, _resources, _registry, camp, workers, worker = _setup_toggle_world()
    camp.set_active(False)

    workers.reassign_all()

    # Even when camp is inactive, lumberjack still heads to workplace and waits there.
    assert worker.state == "moving"
    assert worker.assigned_building is camp
    assert camp.delivered_wood == 0


def test_toggle_off_during_going_to_tree_finishes_current_cycle_then_stops() -> None:
    now_ms, _world, _resources, _registry, camp, workers, worker = _setup_toggle_world()
    _advance_to_chopping(now_ms, workers, worker)
    camp.set_active(False)

    _complete_one_cycle(now_ms, workers)

    assert camp.delivered_wood == 1
    assert worker.state == "working"


def test_toggle_off_during_chopping_finishes_cycle_then_stops() -> None:
    now_ms, _world, _resources, _registry, camp, workers, worker = _setup_toggle_world()
    _advance_to_chopping(now_ms, workers, worker)
    camp.set_active(False)

    _complete_one_cycle(now_ms, workers)

    assert camp.delivered_wood == 1
    assert worker.state == "working"


def test_toggle_off_during_returning_finishes_deposit_then_stops() -> None:
    now_ms, _world, _resources, _registry, camp, workers, worker = _setup_toggle_world()
    _advance_to_chopping(now_ms, workers, worker)
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    assert worker.state == "returning"
    camp.set_active(False)

    _complete_one_cycle(now_ms, workers)

    assert camp.delivered_wood == 1
    assert worker.state == "working"


def test_toggle_off_after_deposit_prevents_next_cycle() -> None:
    now_ms, _world, _resources, _registry, camp, workers, worker = _setup_toggle_world()
    _advance_to_chopping(now_ms, workers, worker)
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "depositing"
    camp.set_active(False)
    workers.update(now_ms[0] + 1)

    assert camp.delivered_wood == 1
    assert worker.state == "working"


def test_toggle_back_on_resumes_cycle_after_reassign() -> None:
    _now_ms, _world, _resources, _registry, camp, workers, worker = _setup_toggle_world()
    camp.set_active(False)
    workers.reassign_all()
    assert worker.state == "moving"

    camp.set_active(True)
    workers.reassign_all()
    # After reassign while moving, target remains unchanged.
    assert worker.state == "moving"
    assert worker.assigned_building is camp
