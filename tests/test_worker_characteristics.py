"""Failing tests for worker characteristics and bonus stacking rules (T92)."""

import pytest

from game.characteristics import Characteristics


def test_characteristics_defaults_are_unity() -> None:
    c = Characteristics()
    assert c.move_speed_mult == 1.0
    assert c.gather_speed_mult == 1.0


def test_add_permanent_replaces_same_source_kind_without_double_stack() -> None:
    c = Characteristics()
    source = ("building_level", 123)
    c.add_permanent(source, "move_speed_mult", 0.05)
    assert c.move_speed_mult == pytest.approx(1.05)
    c.add_permanent(source, "move_speed_mult", 0.10)
    assert c.move_speed_mult == pytest.approx(1.10)


def test_remove_source_undoes_all_permanent_bonuses_from_source() -> None:
    c = Characteristics()
    source = ("building_level", 99)
    c.add_permanent(source, "move_speed_mult", 0.20)
    c.add_permanent(source, "gather_speed_mult", 0.30)
    assert c.move_speed_mult == pytest.approx(1.20)
    assert c.gather_speed_mult == pytest.approx(1.30)
    c.remove_source(source)
    assert c.move_speed_mult == pytest.approx(1.0)
    assert c.gather_speed_mult == pytest.approx(1.0)


def test_temporary_bonus_expires_on_tick_boundary() -> None:
    c = Characteristics()
    c.add_temporary("gather_speed_mult", 0.25, expires_at_ms=5000)
    assert c.gather_speed_mult == pytest.approx(1.25)
    c.tick(4_999)
    assert c.gather_speed_mult == pytest.approx(1.25)
    c.tick(5_000)
    assert c.gather_speed_mult == pytest.approx(1.0)


def test_effective_multipliers_are_clamped_to_positive_minimum() -> None:
    c = Characteristics()
    c.add_permanent(("debuff", 1), "move_speed_mult", -5.0)
    c.add_permanent(("debuff", 1), "gather_speed_mult", -5.0)
    assert c.move_speed_mult == pytest.approx(0.10)
    assert c.gather_speed_mult == pytest.approx(0.10)
