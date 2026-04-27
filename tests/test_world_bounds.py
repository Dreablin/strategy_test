"""World bounds helper should match playable grass field extents."""

from game.config import GRID_SIZE, TILE_H, TILE_W
from game.iso import world_to_screen
from game.render import Renderer
from game.world import World


def test_world_pixel_bounds_include_tree_skirt() -> None:
    world = World()
    min_x, min_y, max_x, max_y = Renderer.world_pixel_bounds(world)

    lo = 0
    hi = GRID_SIZE
    expected_min_x = expected_min_y = 10**9
    expected_max_x = expected_max_y = -10**9
    for gx in range(lo, hi):
        for gy in range(lo, hi):
            sx, sy = world_to_screen(gx, gy)
            expected_min_x = min(expected_min_x, sx)
            expected_min_y = min(expected_min_y, sy)
            expected_max_x = max(expected_max_x, sx + TILE_W)
            expected_max_y = max(expected_max_y, sy + TILE_H)

    assert (min_x, min_y, max_x, max_y) == (
        expected_min_x,
        expected_min_y,
        expected_max_x,
        expected_max_y,
    )
