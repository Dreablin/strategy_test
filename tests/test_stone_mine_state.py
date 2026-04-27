"""Failing tests for StoneMine active toggle and delivery state (T116)."""

import pytest

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall


def test_stone_mine_defaults_active_and_zero_delivered() -> None:
    mine = StoneMine(level=1, grid_pos=(10, 10))
    assert mine.active is True
    assert mine.delivered_stone == 0


def test_stone_mine_toggle_active_flag() -> None:
    mine = StoneMine(level=1, grid_pos=(10, 10))
    mine.set_active(False)
    assert mine.active is False
    mine.set_active(True)
    assert mine.active is True


def test_record_stone_delivered_increments_and_rejects_negative() -> None:
    mine = StoneMine(level=1, grid_pos=(10, 10))
    mine.record_stone_delivered()
    mine.record_stone_delivered(3)
    assert mine.delivered_stone == 4
    with pytest.raises(ValueError):
        mine.record_stone_delivered(-1)


def test_non_stone_mine_buildings_do_not_expose_stone_delivery_api() -> None:
    others = [
        Farm(level=1, grid_pos=(2, 2)),
        LumberCamp(level=1, grid_pos=(4, 4)),
        IronMine(level=1, grid_pos=(6, 6)),
        TownHall(level=1, grid_pos=(8, 8)),
    ]
    for b in others:
        assert not hasattr(b, "record_stone_delivered")
        assert not hasattr(b, "delivered_stone")
