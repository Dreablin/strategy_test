"""Failing tests for Renderer.draw_buildings (Phase 8 T43)."""

from __future__ import annotations

import pygame

from game.assets import grass_tile
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.iso import world_to_screen
from game.render import Renderer
from game.resources import ResourceManager
from game.world import World

_SENTINEL = (20, 24, 22)


def _tile_center_pixel(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + 32, oy + sy + 16


def test_draw_buildings_attribute() -> None:
    assert callable(getattr(Renderer, "draw_buildings", None))


def test_initial_town_hall_drawn() -> None:
    world = World()
    registry = BuildingRegistry(world)
    _resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    surface = pygame.Surface((1280, 720))
    surface.fill(_SENTINEL)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)

    # 3x3 center tile of Town Hall footprint at (16,16) is (17,17).
    px, py = _tile_center_pixel(surface, world, 17, 17)
    color = surface.get_at((px, py))[:3]
    grass_color = grass_tile().get_at((32, 16))[:3]
    assert color != _SENTINEL
    assert color != grass_color


def test_placed_building_drawn() -> None:
    world = World()
    registry = BuildingRegistry(world)
    _resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (20, 20))
    surface = pygame.Surface((1280, 720))
    surface.fill(_SENTINEL)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)

    cx, cy = camp.grid_pos  # type: ignore[assignment]
    px, py = _tile_center_pixel(surface, world, cx + 1, cy + 1)
    color = surface.get_at((px, py))[:3]
    grass_color = grass_tile().get_at((32, 16))[:3]
    assert color != _SENTINEL
    assert color != grass_color


class _Spy:
    """Surface wrapper that records `blit` calls."""

    def __init__(self, inner: pygame.Surface) -> None:
        self.inner = inner
        self.calls: list[tuple[tuple, dict]] = []

    def blit(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.calls.append((args, kwargs))
        return self.inner.blit(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self.inner, name)


def test_painters_order() -> None:
    world = World()
    registry = BuildingRegistry(world)
    _resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    registry.place(LumberCamp, (8, 8))
    registry.place(LumberCamp, (20, 20))
    spy = _Spy(pygame.Surface((1280, 720)))
    Renderer.draw_buildings(spy, world, registry)

    # Building blits should follow painter's order by grid depth.
    dests = [args[1] for args, _kwargs in spy.calls if len(args) >= 2]
    assert len(dests) >= 3
    # Order is (8,8) first, then town hall, then (20,20). We compare the two camps.
    assert dests[0][1] < dests[2][1]


def test_draw_building_shifted_by_camera_offset() -> None:
    world = World()
    registry = BuildingRegistry(world)
    _resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (20, 20))

    no_cam = pygame.Surface((1280, 720))
    no_cam.fill(_SENTINEL)
    Renderer.draw_world(no_cam, world, None)
    Renderer.draw_buildings(no_cam, world, registry, None)

    with_cam = pygame.Surface((1280, 720))
    with_cam.fill(_SENTINEL)
    camera = Camera((50, 30))
    Renderer.draw_world(with_cam, world, camera)
    Renderer.draw_buildings(with_cam, world, registry, camera)

    cx, cy = camp.grid_pos  # type: ignore[assignment]
    px, py = _tile_center_pixel(no_cam, world, cx + 1, cy + 1)
    px2, py2 = px + 50, py + 30
    assert no_cam.get_at((px, py))[:3] != _SENTINEL
    assert with_cam.get_at((px2, py2))[:3] != _SENTINEL
