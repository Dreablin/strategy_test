"""Placement controller: grid snap, spend + registry integration."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.config import BUILD_COST_WOOD, TILE_H, TILE_W
from game.iso import screen_to_world, world_to_screen
from game.render import Renderer
from game.resources import ResourceManager
from game.ui.placement import PlacementController
from game.world import World


def _cell_center_screen(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + TILE_W // 2, oy + sy + TILE_H // 2


def test_place_lumber_camp_deducts_wood() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    placement = PlacementController(world, registry, resources)
    placement.select("LUMBER_CAMP")
    cx, cy = _cell_center_screen(surface, world, 10, 10)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 1
    assert resources.get("wood") == 200 - BUILD_COST_WOOD


def test_cancel_prevents_place() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    placement = PlacementController(world, registry, resources)
    placement.select("LUMBER_CAMP")
    placement.cancel()
    cx, cy = _cell_center_screen(surface, world, 10, 10)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 0
    assert resources.get("wood") == 200


def test_insufficient_wood_does_not_place() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    assert resources.try_spend({"wood": 200 - BUILD_COST_WOOD + 1})
    placement = PlacementController(world, registry, resources)
    placement.select("FARM")
    cx, cy = _cell_center_screen(surface, world, 12, 12)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 0


def test_update_hover_uses_renderer_map_origin() -> None:
    """Hover cell must match `screen_to_world` with the same offset as `Renderer.draw_world`."""
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    placement = PlacementController(world, registry, resources)
    placement.select("LUMBER_CAMP")
    ox, oy = Renderer.map_origin(surface, world)
    mx, my = 512, 360
    placement.update_hover(surface, (mx, my))
    exp = screen_to_world(mx - ox, my - oy)
    assert placement.hover_grid == exp
