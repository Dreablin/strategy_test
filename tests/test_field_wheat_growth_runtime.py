"""RED tests for wheat autonomous growth timing on fields (T227)."""

from __future__ import annotations

from game.buildings import field as field_domain
from game.buildings.field import Field
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def test_wheat_growth_advances_one_phase_every_45_seconds() -> None:
    state = field_domain.WHEAT_PHASE_1
    last_change_ms = 0

    state, last_change_ms = field_domain.advance_wheat_growth(state, last_change_ms, now_ms=44_999)
    assert state == field_domain.WHEAT_PHASE_1
    assert last_change_ms == 0

    state, last_change_ms = field_domain.advance_wheat_growth(state, last_change_ms, now_ms=45_000)
    assert state == field_domain.WHEAT_PHASE_2
    assert last_change_ms == 45_000

    state, last_change_ms = field_domain.advance_wheat_growth(state, last_change_ms, now_ms=90_000)
    assert state == field_domain.WHEAT_PHASE_3
    assert last_change_ms == 90_000

    state, last_change_ms = field_domain.advance_wheat_growth(state, last_change_ms, now_ms=135_000)
    assert state == field_domain.WHEAT_PHASE_4
    assert last_change_ms == 135_000


def test_wheat_growth_does_not_progress_when_field_not_sown() -> None:
    state = field_domain.WHEAT_EMPTY
    last_change_ms = 0

    state, last_change_ms = field_domain.advance_wheat_growth(state, last_change_ms, now_ms=200_000)
    assert state == field_domain.WHEAT_EMPTY
    assert last_change_ms == 0


def test_wheat_growth_catches_up_after_large_time_jump() -> None:
    state, last_change_ms = field_domain.advance_wheat_growth(
        field_domain.WHEAT_PHASE_1,
        0,
        now_ms=135_000,
    )

    assert state == field_domain.WHEAT_PHASE_4
    assert last_change_ms == 135_000


def test_worker_manager_runtime_advances_field_wheat_growth() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, near_town_hall_tile(8, 8))
    field.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])

    field.sow(now_ms=0)
    now_ms["t"] = 44_999
    workers.update(now_ms["t"])
    assert field.wheat_phase == field_domain.WHEAT_PHASE_1

    now_ms["t"] = 45_000
    workers.update(now_ms["t"])
    assert field.wheat_phase == field_domain.WHEAT_PHASE_2

    now_ms["t"] = 135_000
    workers.update(now_ms["t"])
    assert field.wheat_phase == field_domain.WHEAT_PHASE_4
