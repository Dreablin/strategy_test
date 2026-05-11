"""Isometric world/screen coordinate transforms."""

from math import floor

from game.config import TILE_H, TILE_W


def world_to_screen(grid_x: int, grid_y: int) -> tuple[int, int]:
    """Convert grid coordinates to 2:1 isometric screen coordinates."""
    screen_x = (grid_x - grid_y) * (TILE_W // 2)
    screen_y = (grid_x + grid_y) * (TILE_H // 2)
    return screen_x, screen_y


def screen_to_world(screen_x: int, screen_y: int) -> tuple[int, int]:
    """Convert isometric screen coordinates back to integer grid coordinates."""
    half_w = TILE_W // 2
    half_h = TILE_H // 2

    grid_x = (screen_x / half_w + screen_y / half_h) / 2
    grid_y = (screen_y / half_h - screen_x / half_w) / 2
    return int(grid_x), int(grid_y)


def _round_half_up(value: float) -> int:
    return int(floor(value + 0.5))


def screen_to_tile(screen_x: int, screen_y: int) -> tuple[int, int]:
    """Pick the visual isometric tile under a screen pixel.

    ``screen_to_world`` is the inverse of ``world_to_screen``'s top-left
    anchor. Mouse picking needs the tile center instead, otherwise the hover
    jumps to the screen-right neighbor as soon as the cursor crosses the
    visual middle of a diamond.
    """
    half_w = TILE_W // 2
    half_h = TILE_H // 2
    centered_x = screen_x - half_w
    centered_y = screen_y - half_h

    grid_x = (centered_x / half_w + centered_y / half_h) / 2
    grid_y = (centered_y / half_h - centered_x / half_w) / 2
    return _round_half_up(grid_x), _round_half_up(grid_y)
