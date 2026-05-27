"""Tests for worker tier metadata (T340)."""

from __future__ import annotations

from game import config
from game.worker_hiring import HIRABLE_WORKERS
from game.worker_tiers import ALL_TIERS, register_worker_tier, worker_tier, workers_of_tier


def test_worker_tiers_are_loaded_from_game_settings_json() -> None:
    configured = config.SETTINGS["workers"]["tiers"]

    for worker_type, tier in configured.items():
        assert worker_tier(worker_type) == tier


def test_every_hirable_worker_has_tier_and_hire_gate_settings() -> None:
    configured_tiers = set(config.SETTINGS["workers"]["tiers"])
    configured_hire_gates = set(config.SETTINGS["gates"]["hire_min_town_hall_level"])

    assert HIRABLE_WORKERS <= configured_tiers
    assert HIRABLE_WORKERS <= configured_hire_gates


def test_configured_worker_tiers_are_valid() -> None:
    configured = config.SETTINGS["workers"]["tiers"]

    assert configured
    assert set(configured.values()) <= set(ALL_TIERS)


def test_unknown_worker_defaults_to_basic() -> None:
    assert worker_tier("UNKNOWN_TYPE_XYZ") == "basic"


def test_all_tiers_contains_basic_and_advanced() -> None:
    assert "basic" in ALL_TIERS
    assert "advanced" in ALL_TIERS


def test_workers_of_tier_basic_returns_known_workers() -> None:
    basic = workers_of_tier("basic")
    assert "LUMBERJACK" in basic
    assert "CARRIER" in basic
    assert "BUILDER" in basic


def test_workers_of_tier_advanced_contains_winemaker() -> None:
    assert "WINEMAKER" in workers_of_tier("advanced")


def test_register_worker_tier_adds_new_worker() -> None:
    register_worker_tier("TEST_WORKER_TIER", "advanced")
    assert worker_tier("TEST_WORKER_TIER") == "advanced"
    assert "TEST_WORKER_TIER" in workers_of_tier("advanced")
    # Cleanup: reset to basic to not pollute other tests
    register_worker_tier("TEST_WORKER_TIER", "basic")


def test_register_worker_tier_rejects_invalid_tier() -> None:
    import pytest

    with pytest.raises(ValueError, match="unknown tier"):
        register_worker_tier("FOO", "legendary")
