"""Failing tests for renderer viewport culling API and call-count budget (T136)."""

import game.render as render_mod
from game.camera import Camera
from game.config import TILE_H, TILE_W
from game.render import Renderer
from game.world import World

import pygame


def test_visible_tile_range_returns_clipped_inclusive_bounds_with_margin() -> None:
    surface = pygame.Surface((800, 600))
    world = World()
    camera = Camera(initial_offset=(0, 0))

    gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)

    assert 0 <= gx_min <= world.width - 1
    assert 0 <= gy_min <= world.height - 1
    assert 0 <= gx_max <= world.width - 1
    assert 0 <= gy_max <= world.height - 1
    assert gx_max >= gx_min
    assert gy_max >= gy_min


def test_visible_tile_range_can_return_empty_when_camera_far_offscreen() -> None:
    surface = pygame.Surface((800, 600))
    world = World()
    camera = Camera(initial_offset=(1_000_000, 1_000_000))

    gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)

    assert gx_max < gx_min or gy_max < gy_min


def test_visible_tile_count_upper_bound_on_800x600() -> None:
    surface = pygame.Surface((800, 600))
    world = World()
    camera = Camera(initial_offset=(0, 0))

    gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)
    count = max(0, gx_max - gx_min + 1) * max(0, gy_max - gy_min + 1)

    margin = 2
    bound = int((800 / TILE_W) + 2 * margin + 4) * int((600 / TILE_H) + 2 * margin + 4)
    assert count <= bound
    assert count <= 1500


def test_draw_world_world_to_screen_calls_below_budget(monkeypatch) -> None:
    surface = pygame.Surface((800, 600))
    world = World()
    camera = Camera(initial_offset=(0, 0))

    calls = {"n": 0}
    real = render_mod.world_to_screen

    def counted(gx: int, gy: int):
        calls["n"] += 1
        return real(gx, gy)

    monkeypatch.setattr(render_mod, "world_to_screen", counted)
    Renderer.draw_world(surface, world, camera=camera)
    assert calls["n"] < 2000
