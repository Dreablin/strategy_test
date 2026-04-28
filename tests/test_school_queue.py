"""Failing tests for per-school training queue behavior (T163)."""

from __future__ import annotations

from game.buildings.school import School


def _queue_tags(school: School) -> list[str]:
    return [entry.type_tag for entry in school.training_queue()]


def test_school_queue_has_max_seven_slots_and_uses_leftmost_empty() -> None:
    school = School(level=1, grid_pos=(10, 10))
    for worker_type in (
        "LUMBERJACK",
        "STONECUTTER",
        "MINER",
        "FARMER",
        "FORESTER",
        "LUMBERJACK",
        "STONECUTTER",
    ):
        assert school.enqueue_training(worker_type)

    assert len(school.training_queue()) == 7
    assert not school.enqueue_training("MINER")
    assert _queue_tags(school) == [
        "LUMBERJACK",
        "STONECUTTER",
        "MINER",
        "FARMER",
        "FORESTER",
        "LUMBERJACK",
        "STONECUTTER",
    ]


def test_only_front_slot_trains_and_uses_30_seconds_per_unit() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")

    completed = school.update_training(now_ms=29_999)
    assert completed is None
    assert school.training_progress_ms() == 29_999

    completed = school.update_training(now_ms=30_000)
    assert completed == "LUMBERJACK"
    assert _queue_tags(school) == ["FARMER"]
    assert school.training_progress_ms() == 0


def test_multiple_schools_have_independent_queues_and_timers() -> None:
    school_a = School(level=1, grid_pos=(8, 8))
    school_b = School(level=1, grid_pos=(20, 8))
    assert school_a.enqueue_training("LUMBERJACK")
    assert school_a.enqueue_training("FARMER")
    assert school_b.enqueue_training("STONECUTTER")

    assert school_a.update_training(now_ms=30_000) == "LUMBERJACK"
    assert _queue_tags(school_a) == ["FARMER"]
    assert _queue_tags(school_b) == ["STONECUTTER"]
    assert school_b.training_progress_ms() == 0
