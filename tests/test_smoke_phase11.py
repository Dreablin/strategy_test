"""Phase 11 end-to-end smoke test for lumberjack chop/deposit/toggle flow."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def test_smoke_phase11_lumberjack_cycle_toggle_and_reservation() -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    tree_a = (20, 20)
    tree_b = (21, 20)
    world._trees[tree_a] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[tree_b] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    camp = registry.place(LumberCamp, (22, 22))
    now_ms = [0]
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("LUMBERJACK")
    assert worker is not None
    workers.reassign_all()

    # 1-3) Complete first full cycle: walk -> chop -> return -> deposit.
    wood_before = resources.get("wood")
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)

    assert world.tree_at(*tree_a) is None or world.tree_at(*tree_b) is None
    assert resources.get("wood") == wood_before + 1
    assert camp.delivered_wood == 1
    assert worker.state in {"going_to_tree", "idle"}

    # 4) Toggle Off mid-second-cycle: second cycle finishes, no third starts.
    if worker.state == "idle":
        world._trees[tree_a] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
        workers.reassign_all()
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state == "chopping"
    camp.set_active(False)
    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)
    assert camp.delivered_wood == 2
    assert worker.state == "idle"
    assert worker.carrying is None

    # 5) Two camps + two lumberjacks with one tree: only one reservation owner.
    world2 = World()
    world2._trees.clear()  # noqa: SLF001
    lone_tree = (20, 20)
    world2._trees[lone_tree] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    resources2 = ResourceManager()
    registry2 = BuildingRegistry(world2)
    registry2.place(TownHall, (16, 16)).level = 3
    registry2.place(LumberCamp, (22, 22))
    registry2.place(LumberCamp, (26, 22))
    workers2 = WorkerManager(resources2, registry2, now_ms_fn=lambda: 0)
    assert workers2.hire("LUMBERJACK") is not None
    assert workers2.hire("LUMBERJACK") is not None
    workers2.reassign_all()

    reserved_by = [w for w in workers2.workers() if w.target_tree == lone_tree]
    assert len(reserved_by) == 1
    waiting = [w for w in workers2.workers() if w.target_tree is None]
    assert len(waiting) == 1
