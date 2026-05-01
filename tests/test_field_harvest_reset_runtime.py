"""Tests for field harvest reset runtime behavior (T229)."""

from __future__ import annotations

from game.buildings import field as field_domain


def test_harvest_ready_field_resets_immediately_to_empty() -> None:
    state = field_domain.on_field_harvest(field_domain.WHEAT_PHASE_4)
    assert state == field_domain.WHEAT_EMPTY


def test_empty_field_is_immediately_selectable_for_sowing_same_cycle() -> None:
    after_harvest = field_domain.on_field_harvest(field_domain.WHEAT_PHASE_4)
    assert field_domain.is_ready_for_sowing(after_harvest)
    assert field_domain.is_ready_for_sowing(field_domain.WHEAT_EMPTY)


def test_harvest_rejects_non_ripe_phase() -> None:
    try:
        field_domain.on_field_harvest(field_domain.WHEAT_PHASE_3)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError when harvesting non-ripe wheat")
