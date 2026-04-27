"""Failing tests for Lumberjack cycle states (T79)."""

from game.buildings.lumber_camp import LumberCamp
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
    world._trees[(20, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(21, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    camp = registry.place(LumberCamp, (22, 22))
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    return now_ms, world, resources, camp, workers, worker


def test_lumberjack_state_transitions_follow_cycle_order() -> None:
    now_ms, _world, _resources, _camp, workers, worker = _setup_lumberjack_cycle()

    assert worker.state == "idle"
    workers.reassign_all()
    assert worker.state == "going_to_tree"

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"

    now_ms[0] += 10_000
    workers.update(now_ms[0])
    assert worker.state == "returning"

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "depositing"

    now_ms[0] += 1
    workers.update(now_ms[0])
    assert worker.state == "going_to_tree"


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

