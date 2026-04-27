"""Failing tests for Lumber Camp active toggle and delivery counter (T75)."""

import pytest

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall


def test_lumber_camp_defaults_active_and_zero_delivered() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    assert camp.active is True
    assert camp.delivered_wood == 0


def test_lumber_camp_toggle_active_flag() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.set_active(False)
    assert camp.active is False
    camp.set_active(True)
    assert camp.active is True


def test_record_wood_delivered_increments_and_rejects_negative() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.record_wood_delivered()
    camp.record_wood_delivered(3)
    assert camp.delivered_wood == 4
    with pytest.raises(ValueError):
        camp.record_wood_delivered(-1)


def test_non_lumber_buildings_do_not_expose_delivery_api() -> None:
    others = [
        Farm(level=1, grid_pos=(2, 2)),
        StoneMine(level=1, grid_pos=(4, 4)),
        IronMine(level=1, grid_pos=(6, 6)),
        TownHall(level=1, grid_pos=(8, 8)),
    ]
    for b in others:
        assert not hasattr(b, "record_wood_delivered")
        assert not hasattr(b, "delivered_wood")
