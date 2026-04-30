"""RED tests for wheat autonomous growth timing on fields (T227)."""

from __future__ import annotations

from game.buildings import field as field_domain


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
