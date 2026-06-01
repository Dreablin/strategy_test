"""Failing tests for Forester Hut building registration and behavior (T153)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.ui.bottom_bar import _BUTTONS
from game.ui.placement import _TAG_TO_CLASS
from game.world import World


def _forester_hut_cls():
    return _TAG_TO_CLASS["FORESTER_HUT"]


def test_forester_hut_exists_in_build_menu_and_placement_registry() -> None:
    tags = [tag for _, tag in _BUTTONS]
    assert "FORESTER_HUT" in tags
    assert "FORESTER_HUT" in _TAG_TO_CLASS


def test_forester_hut_upgrade_is_rejected_at_fixed_level_one() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 10

    hut = registry.place(_forester_hut_cls(), near_town_hall_tile(8, 8))
    assert hut.level == 1
    assert registry.upgrade_building(hut) is False
    assert hut.level == 1


def test_forester_hut_supports_active_toggle_like_other_camps() -> None:
    hut = _forester_hut_cls()(level=1, grid_pos=(10, 10))
    assert hut.active is True
    hut.set_active(False)
    assert hut.active is False
    hut.set_active(True)
    assert hut.active is True


def test_forester_hut_uses_standard_2x2_producer_placement_rules() -> None:
    cls = _forester_hut_cls()
    assert cls.footprint == (2, 2)

    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    assert registry.can_place(cls, near_town_hall_tile(8, 8))
    assert not registry.can_place(cls, town_hall_origin_tile())
