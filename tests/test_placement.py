"""Placement controller: grid snap, spend + registry integration."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.config import TILE_H, TILE_W
from game.iso import screen_to_world, world_to_screen
from game.render import Renderer
from game.ui.placement import PlacementController
from game.world import World


def _cell_center_screen(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + TILE_W // 2, oy + sy + TILE_H // 2


def test_place_lumber_camp_is_free() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    cx, cy = _cell_center_screen(surface, world, 10, 10)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 1


def test_cancel_prevents_place() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    placement.cancel()
    cx, cy = _cell_center_screen(surface, world, 10, 10)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 0


def test_placement_does_not_require_wallet_resources() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("FARM")
    cx, cy = _cell_center_screen(surface, world, 12, 12)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 1


def test_update_hover_uses_renderer_map_origin() -> None:
    """Hover cell must match `screen_to_world` with the same offset as `Renderer.draw_world`."""
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    ox, oy = Renderer.map_origin(surface, world)
    mx, my = 512, 360
    placement.update_hover(surface, (mx, my))
    exp = screen_to_world(mx - ox, my - oy)
    assert placement.hover_grid == exp
