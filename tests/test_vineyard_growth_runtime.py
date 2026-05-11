"""Vineyard automatic growth after construction (T325)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.config import building_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.world import World
from game.workers import WorkerManager


@pytest.fixture
def fast_vineyard_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    """45s stages are impractical in unit tests."""
    orig = building_int_setting

    def _fake(tag: str, *keys: str) -> int:
        if tag == "VINEYARD" and keys == ("growth", "stage_duration_ms"):
            return 1_000
        return int(orig(tag, *keys))

    monkeypatch.setattr("game.buildings.vineyard.building_int_setting", _fake)


def test_vineyard_first_tick_enters_stage_one(fast_vineyard_growth: None) -> None:
    v = Vineyard(level=1, grid_pos=(1, 1))
    assert v.growth_stage_index() == 0
    v.tick_growth(now_ms=5_000)
    assert v.growth_stage_index() == 1
    assert v.growth_last_change_ms == 5_000
    assert not v.is_ripe()


def test_vineyard_advances_through_stages_and_ripens(fast_vineyard_growth: None) -> None:
    v = Vineyard(level=1, grid_pos=(2, 2))
    v.tick_growth(now_ms=0)
    assert v.growth_stage_index() == 1
    v.tick_growth(now_ms=1_000)
    assert v.growth_stage_index() == 2
    v.tick_growth(now_ms=2_000)
    assert v.growth_stage_index() == 3
    v.tick_growth(now_ms=3_000)
    assert v.growth_stage_index() == 4
    assert v.is_ripe()
    v.tick_growth(now_ms=99_000)
    assert v.growth_stage_index() == 4


def test_vineyard_under_construction_does_not_grow(fast_vineyard_growth: None) -> None:
    v = Vineyard(level=1, grid_pos=(3, 3))
    v.construction_site = ConstructionSite(
        required_resources={"boards": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    v.tick_growth(now_ms=50_000)
    assert v.growth_stage_index() == 0


def test_worker_manager_ticks_registry_vineyards(fast_vineyard_growth: None) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    v = registry.place(Vineyard, near_town_hall_tile(10, 10))
    v.construction_site = None  # completed plot; registry.place starts new builds under construction
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    wm.update(0)
    assert v.growth_stage_index() == 1
    wm.update(1_000)
    assert v.growth_stage_index() == 2
