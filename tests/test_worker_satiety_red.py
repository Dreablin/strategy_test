"""RED tests for worker satiety model (T259).

Expects `game.worker_satiety` helpers used by WorkerManager in T260.
"""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hiring import HIRABLE_WORKERS
from game.worker_models import Worker
from game.worker_satiety import (
    MAX_WORKER_SATIETY,
    SATIETY_DRAIN_PER_GAME_SECOND,
    apply_satiety_game_time,
    clamp_worker_satiety,
)
from game.world import World
from game.workers import WorkerManager


def test_new_worker_starts_at_max_satiety() -> None:
    for type_tag in sorted(HIRABLE_WORKERS):
        assert Worker(type_tag).satiety == MAX_WORKER_SATIETY


@pytest.mark.parametrize("worker_type", sorted(HIRABLE_WORKERS))
def test_hired_worker_starts_at_max_satiety(worker_type: str) -> None:
    world = World(world_seed=3)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5  # hire gates: STONECUTTER 3, MINER 5
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)
    hired = wm.hire(worker_type, source_building=school)
    assert hired is not None, worker_type
    assert hired.satiety == MAX_WORKER_SATIETY


def test_clamp_worker_satiety_max() -> None:
    assert clamp_worker_satiety(MAX_WORKER_SATIETY + 5_000) == MAX_WORKER_SATIETY
    assert clamp_worker_satiety(MAX_WORKER_SATIETY) == MAX_WORKER_SATIETY


def test_clamp_worker_satiety_min() -> None:
    assert clamp_worker_satiety(-1) == 0
    assert clamp_worker_satiety(0) == 0


def test_apply_satiety_game_time_drains_per_whole_second() -> None:
    satiety = MAX_WORKER_SATIETY
    last_ms = 0
    satiety, last_ms = apply_satiety_game_time(satiety, last_ms, 999)
    assert satiety == MAX_WORKER_SATIETY
    assert last_ms == 0
    satiety, last_ms = apply_satiety_game_time(satiety, last_ms, 1000)
    assert satiety == MAX_WORKER_SATIETY - SATIETY_DRAIN_PER_GAME_SECOND
    assert last_ms == 1000


def test_apply_satiety_game_time_no_frame_rate_drift_many_small_steps() -> None:
    """Same total elapsed game time must yield same drain whether stepped or one jump."""
    end = 3_000
    one_step_s, one_step_last = apply_satiety_game_time(MAX_WORKER_SATIETY, 0, end)

    s = MAX_WORKER_SATIETY
    last = 0
    for t in range(50, end + 1, 50):
        s, last = apply_satiety_game_time(s, last, t)
    assert s == one_step_s
    assert last == one_step_last


def test_apply_satiety_game_time_drains_to_zero_not_negative() -> None:
    s = 25
    last = 0
    s, last = apply_satiety_game_time(s, last, 10_000)
    assert s == 0
    assert s >= 0
