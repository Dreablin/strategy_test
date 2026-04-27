"""Tests for World grid, grass zone, and building occupancy."""

import pytest

from game.config import GRID_SIZE
from game.world import World


def _rect_fully_unoccupied(world: World, gx: int, gy: int, w: int, h: int) -> bool:
    return all(
        not world.is_occupied(tx, ty) for tx in range(gx, gx + w) for ty in range(gy, gy + h)
    )


def test_grid_dimensions_match_config() -> None:
    world = World()
    assert world.width == GRID_SIZE == 55
    assert world.height == GRID_SIZE == 55


def test_is_in_grass_playable_field() -> None:
    world = World()
    assert world.is_in_grass(0, 0)
    assert world.is_in_grass(GRID_SIZE - 1, GRID_SIZE - 1)
    assert world.is_in_grass(GRID_SIZE // 2, GRID_SIZE // 2)
    assert not world.is_in_grass(-1, 0)
    assert not world.is_in_grass(0, -1)
    assert not world.is_in_grass(GRID_SIZE, 0)
    assert not world.is_in_grass(0, GRID_SIZE)


@pytest.mark.parametrize(
    ("gx", "gy", "w", "h"),
    [
        (10, 10, 1, 1),
        (0, 0, 2, 2),
        (30, 30, 2, 2),
    ],
)
def test_mark_occupied_covers_entire_footprint(
    gx: int, gy: int, w: int, h: int
) -> None:
    world = World()
    world.mark_occupied(gx, gy, w, h)
    for tx in range(gx, gx + w):
        for ty in range(gy, gy + h):
            assert world.is_occupied(tx, ty)


def test_mark_then_free_clears_footprint() -> None:
    world = World()
    world.mark_occupied(8, 8, 2, 2)
    assert world.is_occupied(8, 8)
    world.free(8, 8, 2, 2)
    assert _rect_fully_unoccupied(world, 8, 8, 2, 2)


def test_unoccupied_region_before_mark() -> None:
    world = World()
    assert _rect_fully_unoccupied(world, 0, 0, 3, 3)


def test_partial_footprint_still_occupied_after_partial_free() -> None:
    world = World()
    world.mark_occupied(5, 5, 2, 2)
    world.free(5, 5, 1, 1)
    assert not world.is_occupied(5, 5)
    assert world.is_occupied(6, 5)
    assert world.is_occupied(5, 6)
    assert world.is_occupied(6, 6)


def test_stone_generation_picks_three_centers_far_from_town_hall() -> None:
    world = World()
    assert len(world._stone_centers) == 3  # noqa: SLF001
    town_hall_tiles = {(x, y) for y in range(16, 19) for x in range(16, 19)}
    for cx, cy in world._stone_centers:  # noqa: SLF001
        assert world.is_in_grass(cx, cy)
        min_dist = min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in town_hall_tiles)
        assert min_dist >= 12


def test_generated_stones_have_units_and_never_overlap_trees() -> None:
    world = World()
    stones = world.iter_stones()
    assert stones
    for (gx, gy), stone in stones:
        assert stone.units == 15
        assert not world.is_tree_blocking(gx, gy)


def test_stone_generation_is_deterministic_for_fresh_world() -> None:
    a = World()
    b = World()
    a_tiles = sorted((pos, stone.units) for pos, stone in a.iter_stones())
    b_tiles = sorted((pos, stone.units) for pos, stone in b.iter_stones())
    assert a_tiles == b_tiles


def test_tree_generation_picks_five_grove_centers_far_from_town_hall() -> None:
    world = World()
    assert len(world._tree_centers) == 5  # noqa: SLF001
    town_hall_tiles = {(x, y) for y in range(16, 19) for x in range(16, 19)}
    for cx, cy in world._tree_centers:  # noqa: SLF001
        assert world.is_in_grass(cx, cy)
        assert not world.is_stone_blocking(cx, cy)
        min_dist = min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in town_hall_tiles)
        assert min_dist >= 12


def test_tree_generation_is_deterministic_for_fresh_world() -> None:
    a = World()
    b = World()
    a_trees = sorted((pos, tree.stage) for pos, tree in a.iter_alive_trees())
    b_trees = sorted((pos, tree.stage) for pos, tree in b.iter_alive_trees())
    assert a_trees == b_trees


def test_scatter_tree_count_matches_two_percent_floor() -> None:
    world = World()
    budget = int(GRID_SIZE * GRID_SIZE * 0.02)
    assert world._scatter_trees_placed == budget  # noqa: SLF001
