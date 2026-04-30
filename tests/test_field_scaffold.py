"""RED tests for FIELD scaffold behavior (T221)."""

from __future__ import annotations

from importlib import import_module

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.pathfinding import find_path_bfs
from game.ui.bottom_bar import _RESOURCE_BUTTONS
from game.world import World


def _require_field_class():
    try:
        module = import_module("game.buildings.field")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Missing FIELD module: {exc}")
    field_cls = getattr(module, "Field", None)
    if field_cls is None:
        pytest.fail("Missing Field class in game.buildings.field")
    return field_cls


def test_field_contract_footprint_and_level_cap() -> None:
    field_cls = _require_field_class()
    assert field_cls.type_tag == "FIELD"
    assert field_cls.footprint == (1, 1)
    assert field_cls.max_level() == 1


def test_field_is_placeable_from_resource_menu() -> None:
    assert any(tag == "FIELD" for (_asset, _label, tag) in _RESOURCE_BUTTONS)


def test_registry_places_field_and_keeps_tile_walkable_for_pathing() -> None:
    field_cls = _require_field_class()
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, (20, 20))

    tile = (8, 8)
    assert registry.can_place(field_cls, tile)
    placed = registry.place(field_cls, tile)
    assert placed.grid_pos == tile
    assert registry.at(*tile) is placed

    blocked = world.blocked_tiles()
    assert tile not in blocked

    path = find_path_bfs(world, (7, 8), (9, 8), blocked)
    assert path is not None
    assert tile in path
