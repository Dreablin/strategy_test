"""Phase 19 integration smoke: place/build/operate/upgrade/resume loop."""

from __future__ import annotations

from game.trees import Tree, TreeStage
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import CHOP_DURATION_MS, WorkerManager


def _tick(workers: WorkerManager, now_ms: dict[str, int], dt_ms: int = 500) -> None:
    now_ms["t"] += dt_ms
    workers.reassign_all()
    workers.update(now_ms["t"])


def _advance_until(
    workers: WorkerManager,
    now_ms: dict[str, int],
    predicate,
    *,
    steps: int = 2400,
    dt_ms: int = 500,
) -> bool:
    for _ in range(steps):
        _tick(workers, now_ms, dt_ms)
        if predicate():
            return True
    return False


def test_smoke_phase19_construction_to_upgrade_cycle() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.add_to_warehouse("wood", 220)
    town_hall.add_to_warehouse("stone", 120)

    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    assert camp.is_under_construction

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    assert workers.hire("CARRIER") is not None
    assert workers.hire("BUILDER") is not None
    lumberjack = workers.hire("LUMBERJACK")
    assert lumberjack is not None

    cx, cy = camp.grid_pos  # type: ignore[assignment]
    world._trees[(cx + 3, cy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(cx + 4, cy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    built_initial = _advance_until(workers, now_ms, lambda: (not camp.is_under_construction))
    assert built_initial, "expected initial construction to complete"
    assert camp.level == 1

    got_lumberjack_assignment = _advance_until(
        workers,
        now_ms,
        lambda: lumberjack.assigned_building is camp,
        steps=1200,
    )
    assert got_lumberjack_assignment, "expected lumberjack to auto-assign after initial construction"

    delivered_before = camp.delivered_wood
    now_ms["t"] += 120_000
    workers.update(now_ms["t"])
    now_ms["t"] += CHOP_DURATION_MS
    workers.update(now_ms["t"])
    now_ms["t"] += 120_000
    workers.update(now_ms["t"])
    workers.update(now_ms["t"] + 1)
    assert camp.delivered_wood >= 1, "expected lumberjack to complete at least one chop/deposit cycle"
    assert camp.delivered_wood >= delivered_before

    assert registry.upgrade_building(camp)
    assert camp.is_under_construction
    assert camp.construction_site is not None
    assert camp.construction_site.target_level == 2
    assert lumberjack.state == "resting"

    built_upgrade = _advance_until(workers, now_ms, lambda: (not camp.is_under_construction), steps=3000)
    assert built_upgrade, "expected level-2 upgrade construction to complete"
    assert camp.level == 2

    resumed_after_upgrade = _advance_until(
        workers,
        now_ms,
        lambda: lumberjack.assigned_building is camp and lumberjack.state != "resting",
        steps=1200,
    )
    assert resumed_after_upgrade, "expected lumberjack to resume after upgrade completion"
