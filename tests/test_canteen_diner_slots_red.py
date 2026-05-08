"""RED tests for canteen diner slot reservations (T263); implementation in T264 (`game.canteen_dining`)."""

from __future__ import annotations

from game.buildings.canteen import CANTEEN_DINER_SLOTS_BASE, Canteen
from game.canteen_dining import (
    count_reserved_diner_slots,
    release_all_diner_slots_for_canteen,
    release_diner_slot_after_meal,
    release_diner_slots_for_worker,
    try_reserve_diner_slot,
)
from game.worker_models import Worker


def _workers(n: int) -> list[Worker]:
    return [Worker("CARRIER", stand_tile=(10 + i, 10)) for i in range(n)]


def test_diner_slot_capacity_by_level_limits_reservations() -> None:
    c1 = Canteen(level=1, grid_pos=(5, 5))
    assert c1.diner_slot_capacity() == CANTEEN_DINER_SLOTS_BASE
    workers = _workers(CANTEEN_DINER_SLOTS_BASE + 1)
    for w in workers[:-1]:
        assert try_reserve_diner_slot(c1, w) is True
    assert count_reserved_diner_slots(c1) == CANTEEN_DINER_SLOTS_BASE
    assert try_reserve_diner_slot(c1, workers[-1]) is False

    c2 = Canteen(level=2, grid_pos=(6, 6))
    cap = CANTEEN_DINER_SLOTS_BASE + 1
    assert c2.diner_slot_capacity() == cap
    ws = _workers(cap + 1)
    for w in ws[:-1]:
        assert try_reserve_diner_slot(c2, w) is True
    assert try_reserve_diner_slot(c2, ws[-1]) is False


def test_reserve_succeeds_when_slot_free() -> None:
    c = Canteen(level=1, grid_pos=(1, 1))
    w = Worker("FARMER", stand_tile=(2, 2))
    assert try_reserve_diner_slot(c, w) is True
    assert count_reserved_diner_slots(c) == 1


def test_same_worker_cannot_reserve_two_slots() -> None:
    c = Canteen(level=3, grid_pos=(3, 3))
    w = Worker("MINER", stand_tile=(4, 4))
    assert try_reserve_diner_slot(c, w) is True
    assert try_reserve_diner_slot(c, w) is False
    assert count_reserved_diner_slots(c) == 1


def test_release_after_meal_frees_slot() -> None:
    c = Canteen(level=1, grid_pos=(7, 7))
    w = Worker("LUMBERJACK", stand_tile=(8, 8))
    assert try_reserve_diner_slot(c, w) is True
    release_diner_slot_after_meal(c, w)
    assert count_reserved_diner_slots(c) == 0
    assert try_reserve_diner_slot(c, w) is True


def test_release_for_worker_clears_reservation() -> None:
    c = Canteen(level=1, grid_pos=(9, 9))
    w = Worker("BUILDER", stand_tile=(10, 10))
    assert try_reserve_diner_slot(c, w) is True
    release_diner_slots_for_worker(w)
    assert count_reserved_diner_slots(c) == 0


def test_release_all_for_canteen_clears_every_slot() -> None:
    c = Canteen(level=2, grid_pos=(11, 11))
    for w in _workers(3):
        assert try_reserve_diner_slot(c, w) is True
    assert count_reserved_diner_slots(c) == 3
    release_all_diner_slots_for_canteen(c)
    assert count_reserved_diner_slots(c) == 0
