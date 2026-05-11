"""Vineyard harvest resets growth cycle (T326)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.config import building_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


@pytest.fixture
def fast_vineyard_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    orig = building_int_setting

    def _fake(tag: str, *keys: str) -> int:
        if tag == "VINEYARD" and keys == ("growth", "stage_duration_ms"):
            return 1_000
        return int(orig(tag, *keys))

    monkeypatch.setattr("game.buildings.vineyard.building_int_setting", _fake)


def test_vineyard_after_harvest_tick_growth_advances_from_stage_one(
    fast_vineyard_growth: None,
) -> None:
    v = Vineyard(level=1, grid_pos=(1, 1))
    v.set_growth_stage(4, now_ms=10_000)
    v.mark_harvested(now_ms=20_000)
    assert v.growth_stage_index() == 1
    v.tick_growth(now_ms=20_000)
    assert v.growth_stage_index() == 1
    v.tick_growth(now_ms=21_000)
    assert v.growth_stage_index() == 2


def test_worker_manager_growth_after_harvest(fast_vineyard_growth: None) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    v = registry.place(Vineyard, near_town_hall_tile(11, 11))
    v.construction_site = None
    v.set_growth_stage(4, now_ms=0)
    v.mark_harvested(now_ms=100_000)
    wm = WorkerManager(registry, now_ms_fn=lambda: 100_000)
    wm.update(100_000)
    assert v.growth_stage_index() == 1
    wm.update(101_000)
    assert v.growth_stage_index() == 2
