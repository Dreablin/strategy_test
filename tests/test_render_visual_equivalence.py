"""Failing pixel-equivalence test for render culling (T138)."""

from __future__ import annotations

import pygame

from game.camera import Camera
from game.render import Renderer
from game.world import World


def _crop_visible_rgba_bytes(surface: pygame.Surface) -> bytes:
    """Crop a 1px border to avoid edge sampling noise across paths."""
    w, h = surface.get_size()
    view = pygame.Surface((w - 2, h - 2), pygame.SRCALPHA)
    view.blit(surface, (0, 0), area=pygame.Rect(1, 1, w - 2, h - 2))
    return pygame.image.tobytes(view, "RGBA")


def test_draw_world_culling_matches_full_grid_pixels(monkeypatch) -> None:
    world = World()
    camera = Camera(initial_offset=(-400, -300))
    size = (320, 240)

    full_surface = pygame.Surface(size, pygame.SRCALPHA)
    cull_surface = pygame.Surface(size, pygame.SRCALPHA)

    # Baseline: bypass culling by forcing full-grid tile bounds.
    monkeypatch.setattr(
        Renderer,
        "visible_tile_range",
        staticmethod(lambda _s, w, _c: (0, 0, w.width - 1, w.height - 1)),
    )
    Renderer.draw_world(full_surface, world, camera)
    Renderer.draw_trees(full_surface, world, camera)
    Renderer.draw_stones(full_surface, world, camera)
    full_bytes = _crop_visible_rgba_bytes(full_surface)

    monkeypatch.undo()

    # New behavior: use culling path.
    Renderer.draw_world(cull_surface, world, camera)
    Renderer.draw_trees(cull_surface, world, camera)
    Renderer.draw_stones(cull_surface, world, camera)
    cull_bytes = _crop_visible_rgba_bytes(cull_surface)

    assert cull_bytes == full_bytes
