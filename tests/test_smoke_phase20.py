"""Phase 20 smoke: SAWYER training, sawmill production, and boards export."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.sawmill import Sawmill
from game.buildings.school import School, SCHOOL_TRAINING_MS
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def _advance_until(
    workers: WorkerManager,
    now_ms: dict[str, int],
    predicate,
    *,
    step_ms: int = 500,
    steps: int = 1200,
) -> bool:
    for _ in range(steps):
        now_ms["t"] += step_ms
        workers.update(now_ms["t"])
        if predicate():
            return True
    return False


def test_smoke_phase20_train_sawyer_produce_and_export_boards() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 8))
    school.construction_site = None
    sawmill.construction_site = None
    town_hall.add_to_warehouse("wood", 3)
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    assert workers.hire("CARRIER") is not None

    assert school.enqueue_training("SAWYER", now_ms=now_ms["t"])
    workers.update(SCHOOL_TRAINING_MS + 1)
    now_ms["t"] = SCHOOL_TRAINING_MS + 1

    sawyer_assigned = _advance_until(
        workers,
        now_ms,
        lambda: any(
            w.type_tag == "SAWYER" and w.assigned_building is sawmill for w in workers.workers()
        ),
    )
    assert sawyer_assigned, "expected trained sawyer assigned to sawmill"

    wood_delivered = _advance_until(workers, now_ms, lambda: sawmill.input_amount() >= 1, steps=2000)
    assert wood_delivered, "expected carrier to refill sawmill wood input"

    boards_made = _advance_until(workers, now_ms, lambda: sawmill.output_amount() >= 1, steps=4000)
    assert boards_made, "expected sawmill to produce at least one board"

    sawyer_rested = _advance_until(
        workers,
        now_ms,
        lambda: any(
            w.type_tag == "SAWYER" and w.assigned_building is sawmill and w.state == "resting"
            for w in workers.workers()
        ),
        steps=800,
    )
    assert sawyer_rested, "expected sawyer to enter mandatory rest after production cycle"

    exported = _advance_until(workers, now_ms, lambda: town_hall.warehouse_amount("boards") >= 1, steps=4000)
    assert exported, "expected carrier to export boards to Town Hall warehouse"
