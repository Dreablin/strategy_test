"""Tests for blocked tile union and no-grid-scan guarantee (T128)."""

import pytest

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.world import World


def test_blocked_tiles_matches_union_after_registry_placement() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    registry.place(LumberCamp, near_town_hall_tile())

    blocked = world.blocked_tiles()
    expected = world.occupied_tiles() | world.tree_tiles() | world.stone_tiles() | world.iron_blocking_tiles()
    assert blocked == expected


def test_blocked_tiles_does_not_call_is_occupied(monkeypatch: pytest.MonkeyPatch) -> None:
    world = World()

    def _fail(*_args, **_kwargs):
        raise pytest.fail("blocked_tiles must not call is_occupied")

    monkeypatch.setattr(World, "is_occupied", _fail)
    blocked = world.blocked_tiles()

    assert blocked == (world.occupied_tiles() | world.tree_tiles() | world.stone_tiles() | world.iron_blocking_tiles())
