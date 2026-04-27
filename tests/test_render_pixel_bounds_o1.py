"""Failing O(1) call-count tests for render pixel bounds (T139)."""

from __future__ import annotations

import game.render as render_mod
from game.config import TILE_H, TILE_W
from game.render import Renderer
from game.world import World

import pygame


def _legacy_world_pixel_bounds(world: World) -> tuple[int, int, int, int]:
    min_x = min_y = 10**9
    max_x = max_y = -10**9
    for gx in range(world.width):
        for gy in range(world.height):
            sx, sy = render_mod.world_to_screen(gx, gy)
            min_x = min(min_x, sx)
            min_y = min(min_y, sy)
            max_x = max(max_x, sx + TILE_W)
            max_y = max(max_y, sy + TILE_H)
    return (min_x, min_y, max_x, max_y)


def _legacy_map_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
    min_x, min_y, max_x, max_y = _legacy_world_pixel_bounds(world)
    cx = (min_x + max_x) // 2
    cy = (min_y + max_y) // 2
    return surface.get_width() // 2 - cx, surface.get_height() // 2 - cy


def test_world_pixel_bounds_and_map_origin_are_o1_and_match_legacy(monkeypatch) -> None:
    world = World()
    surface = pygame.Surface((320, 240))

    calls = {"n": 0}
    real = render_mod.world_to_screen

    def counted(gx: int, gy: int) -> tuple[int, int]:
        calls["n"] += 1
        return real(gx, gy)

    monkeypatch.setattr(render_mod, "world_to_screen", counted)

    bounds = Renderer.world_pixel_bounds(world)
    assert calls["n"] <= 4
    assert bounds == _legacy_world_pixel_bounds(world)

    calls["n"] = 0
    origin = Renderer.map_origin(surface, world)
    assert calls["n"] <= 4
    assert origin == _legacy_map_origin(surface, world)
