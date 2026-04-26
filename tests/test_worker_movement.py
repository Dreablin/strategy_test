"""Failing movement-model tests for Phase 9 (T54)."""

import pytest

import game.config as config
from game.workers import Worker


def test_worker_travel_constant_exists_and_is_3000() -> None:
    assert hasattr(config, "WORKER_TILE_TRAVEL_MS")
    assert config.WORKER_TILE_TRAVEL_MS == 3000


def test_worker_has_path_and_progress_fields() -> None:
    w = Worker("LUMBERJACK", stand_tile=(4, 4))
    assert hasattr(w, "path")
    assert hasattr(w, "segment_progress")
    assert w.path == []
    assert w.segment_progress == pytest.approx(0.0)


def test_worker_state_machine_idle_to_moving_to_working() -> None:
    w = Worker("LUMBERJACK", stand_tile=(2, 2))
    assert w.state == "idle"

    w.start_move([(2, 2), (3, 2), (4, 2)], started_ms=0)
    assert w.state == "moving"

    w.update(now_ms=3000)
    assert w.state == "moving"
    assert w.current_tile == (3, 2)

    w.update(now_ms=6000)
    assert w.state == "working"
    assert w.current_tile == (4, 2)


def test_update_advances_smoothly_per_segment() -> None:
    w = Worker("LUMBERJACK", stand_tile=(1, 1))
    w.start_move([(1, 1), (2, 1)], started_ms=0)

    w.update(now_ms=1500)
    assert 0.45 <= w.segment_progress <= 0.55
    assert w.current_tile == (1, 1)

    w.update(now_ms=2999)
    assert w.current_tile == (1, 1)
    assert w.segment_progress < 1.0

    w.update(now_ms=3000)
    assert w.current_tile == (2, 1)
    assert w.state == "working"
