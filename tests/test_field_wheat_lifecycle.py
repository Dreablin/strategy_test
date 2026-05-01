"""RED tests for wheat lifecycle helpers on fields (T223)."""

from __future__ import annotations

from importlib import import_module


def _field_module():
    return import_module("game.buildings.field")


def test_wheat_phase_constants_exist() -> None:
    field = _field_module()
    assert field.WHEAT_EMPTY == "EMPTY"
    assert field.WHEAT_PHASE_1 == "PHASE_1"
    assert field.WHEAT_PHASE_2 == "PHASE_2"
    assert field.WHEAT_PHASE_3 == "PHASE_3"
    assert field.WHEAT_PHASE_4 == "PHASE_4"


def test_wheat_progression_helper_advances_until_ripe() -> None:
    field = _field_module()
    assert field.next_wheat_phase(field.WHEAT_EMPTY) == field.WHEAT_PHASE_1
    assert field.next_wheat_phase(field.WHEAT_PHASE_1) == field.WHEAT_PHASE_2
    assert field.next_wheat_phase(field.WHEAT_PHASE_2) == field.WHEAT_PHASE_3
    assert field.next_wheat_phase(field.WHEAT_PHASE_3) == field.WHEAT_PHASE_4
    assert field.next_wheat_phase(field.WHEAT_PHASE_4) == field.WHEAT_PHASE_4


def test_wheat_reset_after_harvest_returns_empty() -> None:
    field = _field_module()
    assert field.reset_after_harvest(field.WHEAT_PHASE_4) == field.WHEAT_EMPTY


def test_field_owns_wheat_phase_and_growth_timestamp() -> None:
    field = _field_module()
    crop = field.Field()

    assert crop.wheat_phase == field.WHEAT_EMPTY
    crop.sow(now_ms=1_000)
    assert crop.wheat_phase == field.WHEAT_PHASE_1
    assert crop.wheat_last_change_ms == 1_000

    crop.update_wheat_growth(46_000)
    assert crop.wheat_phase == field.WHEAT_PHASE_2
    assert crop.wheat_last_change_ms == 46_000

    crop.harvest(now_ms=200_000)
    assert crop.wheat_phase == field.WHEAT_EMPTY
    assert crop.wheat_last_change_ms == 200_000
