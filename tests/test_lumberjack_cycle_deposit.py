"""Failing tests for Lumberjack deposit and delivery counters (T83)."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _setup_single_cycle():
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._trees[(20, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(21, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    camp = registry.place(LumberCamp, (22, 22))
    camp.level = 5
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    workers.reassign_all()
    return now_ms, world, resources, camp, workers, worker


def test_wood_added_only_on_deposit_not_on_chop_or_pickup() -> None:
    now_ms, _world, resources, _camp, workers, worker = _setup_single_cycle()
    wood0 = resources.get("wood")

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    assert resources.get("wood") == wood0

    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    assert worker.state in {"returning", "depositing"}
    assert worker.carrying == "wood"
    assert resources.get("wood") == wood0

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "depositing"
    workers.update(now_ms[0] + 1)
    assert resources.get("wood") == wood0 + 1


def test_full_cycle_adds_exactly_one_wood_even_high_level_camp() -> None:
    now_ms, _world, resources, camp, workers, worker = _setup_single_cycle()
    wood0 = resources.get("wood")
    delivered0 = camp.delivered_wood

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert worker.carrying is None
    assert resources.get("wood") == wood0 + 1
    assert camp.delivered_wood == delivered0 + 1


def test_two_camps_track_deliveries_independently() -> None:
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._trees[(20, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(30, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(21, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(29, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    camp_a = registry.place(LumberCamp, (22, 22))
    camp_b = registry.place(LumberCamp, (26, 22))
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    assert workers.hire("LUMBERJACK") is not None
    assert workers.hire("LUMBERJACK") is not None
    workers.reassign_all()

    wood0 = resources.get("wood")
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert camp_a.delivered_wood == 1
    assert camp_b.delivered_wood == 1
    assert resources.get("wood") == wood0 + 2


def test_lumberjack_does_not_start_next_cycle_when_storage_full() -> None:
    now_ms, _world, resources, camp, workers, worker = _setup_single_cycle()
    camp.stored = camp.storage_capacity()
    wood_before = resources.get("wood")
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
    assert resources.get("wood") == wood_before
    assert camp.delivered_wood == delivered_before
