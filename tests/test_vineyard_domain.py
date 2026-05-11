"""Vineyard plot domain (T320+): footprint, growth fields, accessors; growth via ``tick_growth`` (T325)."""

from __future__ import annotations

import pytest

from game.buildings.vineyard import Vineyard
from game.config import building_int_setting


def test_vineyard_type_tag_and_footprint() -> None:
    assert Vineyard.type_tag == "VINEYARD"
    assert Vineyard.footprint == (1, 1)


def test_vineyard_growth_settings_match_json() -> None:
    v = Vineyard(level=1, grid_pos=(5, 5))
    assert v.growth_stage_count() == building_int_setting("VINEYARD", "growth", "stage_count")
    assert v.stage_duration_ms() == building_int_setting("VINEYARD", "growth", "stage_duration_ms")
    assert v.growth_stage_count() == 4
    assert v.stage_duration_ms() == 45_000


def test_vineyard_max_level_matches_global_cap() -> None:
    Vineyard(level=10)
    with pytest.raises(ValueError):
        Vineyard(level=11)


def test_vineyard_starts_not_ripe_stage_zero() -> None:
    v = Vineyard(level=1, grid_pos=(1, 1))
    assert v.growth_stage_index() == 0
    assert not v.is_ripe()


def test_vineyard_set_growth_stage_and_ripe() -> None:
    v = Vineyard(level=1, grid_pos=(2, 2))
    v.set_growth_stage(3, now_ms=1_000)
    assert v.growth_stage_index() == 3
    assert not v.is_ripe()
    v.set_growth_stage(4, now_ms=2_000)
    assert v.is_ripe()


def test_vineyard_set_growth_stage_rejects_out_of_range() -> None:
    v = Vineyard(level=1, grid_pos=(2, 2))
    with pytest.raises(ValueError):
        v.set_growth_stage(5)
    with pytest.raises(ValueError):
        v.set_growth_stage(-1)


def test_vineyard_mark_harvested_restarts_at_stage_one() -> None:
    v = Vineyard(level=1, grid_pos=(2, 2))
    v.set_growth_stage(4, now_ms=5_000)
    assert v.is_ripe()
    v.mark_harvested(now_ms=6_000)
    assert v.growth_stage_index() == 1
    assert v.growth_last_change_ms == 6_000
    assert not v.is_ripe()


def test_vineyard_mark_harvested_requires_ripe() -> None:
    v = Vineyard(level=1, grid_pos=(2, 2))
    with pytest.raises(ValueError, match="not ripe"):
        v.mark_harvested(now_ms=1_000)


def test_vineyard_mark_harvested_rejects_under_construction() -> None:
    from game.construction import ConstructionSite

    v = Vineyard(level=1, grid_pos=(2, 2))
    v.set_growth_stage(4, now_ms=5_000)
    v.construction_site = ConstructionSite(
        required_resources={"boards": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    with pytest.raises(ValueError, match="under construction"):
        v.mark_harvested(now_ms=6_000)
