"""Tests for world/screen isometric coordinate transforms."""

import pytest

from game.config import TILE_H, TILE_W
from game.iso import screen_to_tile, screen_to_world, world_to_screen


@pytest.mark.parametrize(
    ("grid_x", "grid_y"),
    [
        (0, 0),
        (1, 0),
        (0, 1),
        (5, 7),
        (31, 31),
    ],
)
def test_world_screen_round_trip(grid_x: int, grid_y: int) -> None:
    screen_x, screen_y = world_to_screen(grid_x, grid_y)
    round_trip_x, round_trip_y = screen_to_world(screen_x, screen_y)
    assert (round_trip_x, round_trip_y) == (grid_x, grid_y)


def test_screen_to_tile_uses_visual_diamond_center() -> None:
    gx, gy = 10, 12
    sx, sy = world_to_screen(gx, gy)
    center = (sx + TILE_W // 2, sy + TILE_H // 2)

    assert screen_to_tile(*center) == (gx, gy)


def test_screen_to_tile_keeps_right_half_inside_same_diamond() -> None:
    gx, gy = 10, 12
    sx, sy = world_to_screen(gx, gy)
    center_x = sx + TILE_W // 2
    center_y = sy + TILE_H // 2

    assert screen_to_tile(center_x + TILE_W // 2 - 1, center_y) == (gx, gy)


def test_screen_to_tile_moves_right_after_diamond_edge() -> None:
    gx, gy = 10, 12
    sx, sy = world_to_screen(gx, gy)
    center_x = sx + TILE_W // 2
    center_y = sy + TILE_H // 2

    assert screen_to_tile(center_x + TILE_W // 2 + 1, center_y) == (gx + 1, gy - 1)
