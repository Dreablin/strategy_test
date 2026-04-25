"""Isometric world drawing (grass field and decorative tree skirt)."""

import pygame

from game.assets import grass_tile, tree_tile
from game.config import TILE_H, TILE_W
from game.iso import world_to_screen
from game.world import World

_TREE_RING_TILES = 2


def _compute_grass_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
    """Shift so the playable grass patch is roughly centered on the surface."""
    min_x = min_y = 10**9
    max_x = max_y = -10**9
    for gx in range(world.width):
        for gy in range(world.height):
            sx, sy = world_to_screen(gx, gy)
            min_x = min(min_x, sx)
            min_y = min(min_y, sy)
            max_x = max(max_x, sx + TILE_W)
            max_y = max(max_y, sy + TILE_H)
    cx = (min_x + max_x) // 2
    cy = (min_y + max_y) // 2
    return surface.get_width() // 2 - cx, surface.get_height() // 2 - cy


class Renderer:
    """Draws the static grass map plus an outer ring of non-playable tree tiles."""

    @staticmethod
    def map_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
        """Screen offset for `world_to_screen` so the grass patch matches `draw_world`."""
        return _compute_grass_origin(surface, world)

    @staticmethod
    def draw_world(surface: pygame.Surface, world: World) -> None:
        origin_x, origin_y = Renderer.map_origin(surface, world)
        lo = -_TREE_RING_TILES
        hi_w = world.width + _TREE_RING_TILES
        hi_h = world.height + _TREE_RING_TILES

        cells: list[tuple[int, int, bool]] = []
        for gx in range(lo, hi_w):
            for gy in range(lo, hi_h):
                cells.append((gx, gy, world.is_in_grass(gx, gy)))
        cells.sort(key=lambda c: (c[0] + c[1], c[0]))

        g_tile = grass_tile()
        t_tile = tree_tile()
        for gx, gy, in_grass in cells:
            sx, sy = world_to_screen(gx, gy)
            tile = g_tile if in_grass else t_tile
            surface.blit(tile, (origin_x + sx, origin_y + sy))
