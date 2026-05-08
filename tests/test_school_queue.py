"""Failing tests for per-school training queue behavior (T163)."""

from __future__ import annotations

from game.buildings.school import SCHOOL_QUEUE_CAPACITY, SCHOOL_TRAINING_MS, School


def _queue_tags(school: School) -> list[str]:
    return [entry.type_tag for entry in school.training_queue()]


def test_school_queue_uses_configured_capacity_and_leftmost_empty() -> None:
    school = School(level=1, grid_pos=(10, 10))
    pattern = (
        "LUMBERJACK",
        "STONECUTTER",
        "MINER",
        "FARMER",
        "FORESTER",
    )
    worker_types = [pattern[i % len(pattern)] for i in range(SCHOOL_QUEUE_CAPACITY)]
    for worker_type in worker_types:
        assert school.enqueue_training(worker_type)

    assert len(school.training_queue()) == SCHOOL_QUEUE_CAPACITY
    assert not school.enqueue_training("MINER")
    assert _queue_tags(school) == worker_types


def test_only_front_slot_trains_and_uses_configured_training_duration() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")

    completed = school.update_training(now_ms=SCHOOL_TRAINING_MS - 1)
    assert completed is None
    assert school.training_progress_ms() == SCHOOL_TRAINING_MS - 1

    completed = school.update_training(now_ms=SCHOOL_TRAINING_MS)
    assert completed == "LUMBERJACK"
    assert _queue_tags(school) == ["FARMER"]
    assert school.training_progress_ms() == 0


def test_multiple_schools_have_independent_queues_and_timers() -> None:
    school_a = School(level=1, grid_pos=(8, 8))
    school_b = School(level=1, grid_pos=(20, 8))
    assert school_a.enqueue_training("LUMBERJACK")
    assert school_a.enqueue_training("FARMER")
    assert school_b.enqueue_training("STONECUTTER")

    assert school_a.update_training(now_ms=SCHOOL_TRAINING_MS) == "LUMBERJACK"
    assert _queue_tags(school_a) == ["FARMER"]
    assert _queue_tags(school_b) == ["STONECUTTER"]
    assert school_b.training_progress_ms() == 0


def test_front_training_does_not_complete_instantly_with_large_now_ms() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")

    # In runtime, now_ms is often already large (pygame ticks).
    # First update should only initialize start time, not complete immediately.
    assert school.update_training(now_ms=1_000_000) is None
    assert school.training_progress_ms() == 0
    assert len(school.training_queue()) == 1


def test_cancel_training_at_shifts_queue_left_and_resets_front_progress() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")
    assert school.enqueue_training("MINER")
    assert school.update_training(now_ms=10_000) is None
    assert school.training_progress_ms() == 10_000

    assert school.cancel_training_at(1)
    assert _queue_tags(school) == ["LUMBERJACK", "MINER"]
    assert school.training_progress_ms() == 10_000

    assert school.cancel_training_at(0)
    assert _queue_tags(school) == ["MINER"]
    assert school.training_progress_ms() == 0

    assert school.cancel_training_at(0)
    assert _queue_tags(school) == []
    assert school.training_progress_ms() == 0


def test_cancel_active_training_resets_progress_with_nonzero_now_ms() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK", now_ms=5_000)
    assert school.enqueue_training("FARMER")
    assert school.update_training(now_ms=20_000) is None
    assert school.training_progress_ms() == 15_000

    assert school.cancel_training_at(0, now_ms=20_000)
    assert _queue_tags(school) == ["FARMER"]
    assert school.training_progress_ms() == 0

    assert school.update_training(now_ms=20_001) is None
    assert school.training_progress_ms() == 1
