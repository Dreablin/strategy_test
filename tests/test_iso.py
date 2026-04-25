"""Tests for world/screen isometric coordinate transforms."""

import pytest

from game.iso import screen_to_world, world_to_screen


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
