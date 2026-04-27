"""Failing tests for stone domain model and world stone API (T108)."""

import pytest

from game.stones import Stone
from game.world import World


def test_stone_harvest_decrements_units_and_reports_depletion() -> None:
    stone = Stone()
    assert stone.units == 15
    for expected in range(14, -1, -1):
        assert stone.harvest() == expected
    assert stone.is_depleted


def test_stone_harvest_raises_when_empty() -> None:
    stone = Stone(units=1)
    assert stone.harvest() == 0
    with pytest.raises(ValueError):
        stone.harvest()


def test_world_stone_lookup_and_blocking_and_iteration() -> None:
    world = World()
    world._stones = {(5, 6): Stone()}  # noqa: SLF001

    stone = world.stone_at(5, 6)
    assert stone is not None
    assert world.is_stone_blocking(5, 6)
    entries = world.iter_stones()
    assert ((5, 6), stone) in entries


def test_world_harvest_stone_removes_when_depleted() -> None:
    world = World()
    world._stones = {(2, 3): Stone(units=1)}  # noqa: SLF001

    harvested = world.harvest_stone(2, 3)
    assert harvested is not None
    assert harvested.units == 0
    assert world.stone_at(2, 3) is None
    assert not world.is_stone_blocking(2, 3)


def test_world_stone_reservation_api_mirrors_tree_behavior() -> None:
    world = World()
    worker_a = object()
    worker_b = object()
    world._stones = {(7, 8): Stone()}  # noqa: SLF001

    assert world.reserve_stone(7, 8, worker_a) is True
    assert world.reserve_stone(7, 8, worker_b) is False
    assert world.reserve_stone(7, 8, worker_a) is True
    assert world.is_stone_reserved(7, 8) is True

    world.release_stone(7, 8)
    assert world.is_stone_reserved(7, 8) is False

    assert world.reserve_stone(7, 8, worker_b) is True
    world.release_reservations_for(worker_b)
    assert world.is_stone_reserved(7, 8) is False
