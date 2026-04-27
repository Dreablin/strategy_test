"""Failing tests for Lumberjack gather-speed scaling (T98)."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _setup_lumberjack(level: int):
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._trees[(20, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(21, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    camp = registry.place(LumberCamp, (22, 22))
    camp.level = level
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    workers.reassign_all()
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    return now_ms, workers, worker


def test_level1_chop_duration_uses_default_duration() -> None:
    now_ms, workers, worker = _setup_lumberjack(level=1)
    now_ms[0] += CHOP_DURATION_MS - 1
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    now_ms[0] += 1
    workers.update(now_ms[0])
    assert worker.state in {"returning", "depositing"}


def test_level5_gather_bonus_shortens_chop_with_rounded_duration() -> None:
    now_ms, workers, worker = _setup_lumberjack(level=5)
    effective_ms = int(round(CHOP_DURATION_MS / 1.20))
    assert effective_ms == 8333
    now_ms[0] += effective_ms - 1
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    now_ms[0] += 1
    workers.update(now_ms[0])
    assert worker.state in {"returning", "depositing"}
