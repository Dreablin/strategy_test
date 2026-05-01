"""RED tests for farmer field target priority selection (T231)."""

from __future__ import annotations

import game.workers as workers_mod
from game.buildings import field as field_domain


def test_select_farmer_target_prefers_ripe_field_over_empty_within_radius() -> None:
    farm_home = (20, 20)
    field_phases = {
        (24, 20): field_domain.WHEAT_EMPTY,
        (22, 21): field_domain.WHEAT_PHASE_4,
    }
    picked = workers_mod.select_farmer_field_target(
        farm_home=farm_home,
        field_phases=field_phases,
        max_radius=10,
    )
    assert picked == (22, 21)


def test_select_farmer_target_falls_back_to_empty_when_no_ripe_exists() -> None:
    farm_home = (30, 30)
    field_phases = {
        (31, 30): field_domain.WHEAT_PHASE_2,
        (33, 34): field_domain.WHEAT_EMPTY,
    }
    picked = workers_mod.select_farmer_field_target(
        farm_home=farm_home,
        field_phases=field_phases,
        max_radius=10,
    )
    assert picked == (33, 34)


def test_select_farmer_target_returns_none_when_no_supported_field_state_in_radius() -> None:
    farm_home = (40, 40)
    field_phases = {
        (51, 40): field_domain.WHEAT_PHASE_4,  # outside Chebyshev radius 10
        (39, 39): field_domain.WHEAT_PHASE_2,  # inside but not actionable
    }
    picked = workers_mod.select_farmer_field_target(
        farm_home=farm_home,
        field_phases=field_phases,
        max_radius=10,
    )
    assert picked is None
