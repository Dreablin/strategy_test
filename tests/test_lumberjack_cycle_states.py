"""Failing tests for Lumberjack cycle states (T79)."""

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import WorkerManager


def _setup_lumberjack_cycle():
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 3
    camp = registry.place(LumberCamp, near_town_hall_tile())
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    world._trees[(gx + 3, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(gx + 4, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    return now_ms, world, resources, camp, workers, worker


def test_lumberjack_state_transitions_follow_cycle_order() -> None:
    now_ms, _world, _resources, _camp, workers, worker = _setup_lumberjack_cycle()

    assert worker.state == "idle"
    workers.reassign_all()
    # Lumberjack first walks to the camp (no tree picked yet).
    assert worker.state == "moving"
    assert worker.target_tree is None

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    # One large tick covers walk-to-camp + cycle start + walk-to-tree + chop start.
    assert worker.state == "chopping"
    assert worker.target_tree is not None

    now_ms[0] += 10_000
    workers.update(now_ms[0])
    assert worker.state == "returning"

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "depositing"

    now_ms[0] += 1
    workers.update(now_ms[0])
    assert worker.state == "working"


def test_lumberjack_carrying_wood_toggles_on_chop_and_off_on_deposit() -> None:
    now_ms, _world, _resources, _camp, workers, worker = _setup_lumberjack_cycle()
    workers.reassign_all()
    assert worker.carrying is None

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    assert worker.carrying is None

    now_ms[0] += 10_000
    workers.update(now_ms[0])
    assert worker.carrying == "wood"
    assert worker.state == "returning"

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "depositing"

    now_ms[0] += 1
    workers.update(now_ms[0])
    assert worker.carrying is None


def test_lumberjack_waits_inside_camp_before_first_exit() -> None:
    now_ms, _world, _resources, _camp, workers, worker = _setup_lumberjack_cycle()
    workers.reassign_all()

    # Reach the camp first.
    while worker.state == "moving":
        now_ms[0] += 3_000
        workers.update(now_ms[0])
    assert worker.state == "working"
    assert worker.target_tree is None

    workers.update(worker.camp_wait_until_ms - 1)
    assert worker.state == "working"
    assert worker.target_tree is None

    workers.update(worker.camp_wait_until_ms)
    assert worker.state in {"going_to_tree", "chopping"}
    assert worker.target_tree is not None


def test_lumberjack_waits_inside_camp_after_deposit_before_next_exit() -> None:
    now_ms, _world, _resources, _camp, workers, worker = _setup_lumberjack_cycle()
    workers.reassign_all()

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += 10_000
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert worker.state == "working"
    assert worker.target_tree is None
    wait_until = worker.camp_wait_until_ms

    workers.update(wait_until - 1)
    assert worker.state == "working"
    assert worker.target_tree is None

    workers.update(wait_until)
    assert worker.state in {"going_to_tree", "chopping"}

