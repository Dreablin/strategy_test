"""Tests for TickScheduler (10 s production cycle boundary)."""

from game.config import TICK_MS
from game.tick import TickScheduler


def test_no_tick_before_first_boundary() -> None:
    sched = TickScheduler()
    assert not sched.update(0)
    assert not sched.update(TICK_MS // 2)
    assert not sched.update(TICK_MS - 1)


def test_tick_true_once_at_first_boundary() -> None:
    sched = TickScheduler()
    assert sched.update(TICK_MS)
    assert not sched.update(TICK_MS)


def test_false_between_boundaries() -> None:
    sched = TickScheduler()
    assert sched.update(TICK_MS)
    assert not sched.update(TICK_MS + 1)
    assert not sched.update(2 * TICK_MS - 1)


def test_tick_true_again_at_second_boundary() -> None:
    sched = TickScheduler()
    assert sched.update(TICK_MS)
    assert not sched.update(TICK_MS + 5000)
    assert sched.update(2 * TICK_MS)


def test_single_true_per_boundary_across_updates() -> None:
    sched = TickScheduler()
    assert not sched.update(1000)
    assert not sched.update(5000)
    assert sched.update(TICK_MS)
    assert not sched.update(TICK_MS + 4000)
    assert sched.update(2 * TICK_MS)
    assert not sched.update(2 * TICK_MS)


def test_large_jump_fires_once() -> None:
    """One update call yields at most one tick signal."""
    sched = TickScheduler()
    assert sched.update(3 * TICK_MS)
    assert not sched.update(3 * TICK_MS)
