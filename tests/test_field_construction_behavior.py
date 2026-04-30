"""RED tests for FIELD-specific construction behavior (T224)."""

from __future__ import annotations

from game.buildings.field import Field
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def _advance(workers: WorkerManager, now_ms: dict[str, int], *, steps: int, step_ms: int = 500) -> None:
    for _ in range(steps):
        now_ms["t"] += step_ms
        workers.reassign_all()
        workers.update(now_ms["t"])


def test_field_builder_targets_field_tile_not_adjacent_tile() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, (8, 8))
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    builder = workers.hire("BUILDER")
    assert builder is not None

    _advance(workers, now_ms, steps=30)

    assert builder.assigned_building is field
    assert builder.target_tile == (8, 8)


def test_field_builder_stands_on_field_tile_while_building_and_finishes_in_10s() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, (10, 10))
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    builder = workers.hire("BUILDER")
    assert builder is not None
    assert field.construction_site is not None
    assert field.construction_site.build_time_ms == 10_000

    _advance(workers, now_ms, steps=40)

    assert field.construction_site is not None
    assert field.construction_site.builder is builder
    assert builder.current_tile == (10, 10)

    # Not complete before full 10s window.
    workers.update(field.construction_site.build_started_ms + 9_999)
    assert field.is_under_construction

    workers.update(field.construction_site.build_started_ms + 10_000)
    assert not field.is_under_construction
