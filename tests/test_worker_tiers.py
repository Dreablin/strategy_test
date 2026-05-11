"""Tests for worker tier metadata (T340)."""

from __future__ import annotations

from game.worker_tiers import ALL_TIERS, register_worker_tier, worker_tier, workers_of_tier


def test_all_existing_workers_are_basic() -> None:
    known_basic = [
        "LUMBERJACK", "STONECUTTER", "MINER", "FARMER",
        "ANIMAL_HERDER", "FORESTER", "SAWYER", "MILLER",
        "BAKER", "COOK", "WATERMAN", "CARRIER", "BUILDER",
    ]
    for wt in known_basic:
        assert worker_tier(wt) == "basic", f"{wt} should be basic"


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


def test_workers_of_tier_advanced_initially_empty() -> None:
    assert workers_of_tier("advanced") == []


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
