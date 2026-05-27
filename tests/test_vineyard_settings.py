"""Vineyard plot behavior tests."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World


def test_vineyard_plot_does_not_block_its_tile() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    tile = near_town_hall_tile(12, 8)
    plot = registry.place(Vineyard, tile)

    assert plot.grid_pos == tile
    assert not world.is_occupied(*tile)
    assert tile not in world.blocked_tiles()
