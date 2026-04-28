"""Failing tests for Lumberjack chopping interaction (T81)."""

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _setup_two_tree_cycle():
    now_ms = [0]
    world = World(world_seed=2)
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
    workers.reassign_all()
    return now_ms, world, resources, registry, camp, workers, worker


def test_chop_duration_removes_tree_and_releases_reservation() -> None:
    now_ms, world, _resources, _registry, _camp, workers, worker = _setup_two_tree_cycle()

    # Right after reassign_all the worker is still walking to the camp.
    assert worker.state == "moving"
    assert worker.target_tree is None

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    tree_tile = worker.target_tree
    assert tree_tile is not None
    assert world.tree_at(*tree_tile) is not None

    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    assert world.tree_at(*tree_tile) is None
    assert not world.is_tree_blocking(*tree_tile)
    assert world.is_tree_reserved(*tree_tile) is False


def test_level1_chop_completes_on_exact_chop_duration_boundary() -> None:
    now_ms, _world, _resources, _registry, _camp, workers, worker = _setup_two_tree_cycle()
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"

    now_ms[0] += CHOP_DURATION_MS - 1
    workers.update(now_ms[0])
    assert worker.state == "chopping"

    now_ms[0] += 1
    workers.update(now_ms[0])
    assert worker.state in {"returning", "depositing"}


def test_second_lumberjack_can_target_another_tree_same_cycle() -> None:
    now_ms, world, resources, registry, camp_a, workers, worker_a = _setup_two_tree_cycle()
    camp_b = registry.place(LumberCamp, near_town_hall_tile(18, 2))
    bx, by = camp_b.grid_pos  # type: ignore[assignment]
    world._trees[(bx + 3, by)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(bx + 4, by)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    worker_b = workers.hire("LUMBERJACK")
    assert worker_b is not None
    workers.reassign_all()

    now_ms[0] += 120_000
    workers.update(now_ms[0])

    # Both workers have reached their respective camps and started chopping
    # on distinct tree targets.
    assert worker_a.target_tree is not None
    assert worker_b.target_tree is not None
    assert worker_a.target_tree != worker_b.target_tree

    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])

    # During same cycle, both workers should be active on distinct targets.
    assert worker_a.state in {"returning", "depositing"}
    assert worker_b.state in {"chopping", "returning", "depositing"}
    assert resources.get("wood") >= 200


def test_demolish_during_chopping_cancels_without_tree_cut_or_deposit() -> None:
    now_ms, world, resources, registry, camp, workers, worker = _setup_two_tree_cycle()

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    tree_tile = worker.target_tree
    assert tree_tile is not None

    registry.demolish(camp, workers)
    assert worker.state == "idle"
    assert worker.carrying is None
    assert world.tree_at(*tree_tile) is not None
    wood_before = resources.get("wood")

    now_ms[0] += CHOP_DURATION_MS + 1
    workers.update(now_ms[0])
    assert world.tree_at(*tree_tile) is not None
    assert resources.get("wood") == wood_before
