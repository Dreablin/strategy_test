"""Failing tests for Lumberjack chopping interaction (T81)."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _setup_two_tree_cycle():
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
    workers.reassign_all()
    return now_ms, world, resources, registry, camp, workers, worker


def test_chop_duration_removes_tree_and_releases_reservation() -> None:
    now_ms, world, _resources, _registry, _camp, workers, worker = _setup_two_tree_cycle()

    tree_tile = worker.target_tree
    assert tree_tile is not None
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    assert world.tree_at(*tree_tile) is not None

    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    assert world.tree_at(*tree_tile) is None
    assert not world.is_tree_blocking(*tree_tile)
    assert world.is_tree_reserved(*tree_tile) is False


def test_second_lumberjack_can_target_another_tree_same_cycle() -> None:
    now_ms, _world, resources, registry, _camp, workers, worker_a = _setup_two_tree_cycle()

    worker_b = workers.hire("LUMBERJACK")
    assert worker_b is not None
    workers.reassign_all()
    assert worker_a.target_tree is not None
    assert worker_b.target_tree is not None
    assert worker_a.target_tree != worker_b.target_tree

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])

    # During same cycle, both workers should be active on distinct targets.
    assert worker_a.state in {"returning", "depositing"}
    assert worker_b.state in {"chopping", "returning", "depositing"}
    assert resources.get("wood") >= 200


def test_demolish_during_chopping_cancels_without_tree_cut_or_deposit() -> None:
    now_ms, world, resources, registry, camp, workers, worker = _setup_two_tree_cycle()

    tree_tile = worker.target_tree
    assert tree_tile is not None
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"

    registry.demolish(camp, workers)
    assert worker.state == "idle"
    assert worker.carrying is None
    assert world.tree_at(*tree_tile) is not None
    wood_before = resources.get("wood")

    now_ms[0] += CHOP_DURATION_MS + 1
    workers.update(now_ms[0])
    assert world.tree_at(*tree_tile) is not None
    assert resources.get("wood") == wood_before
