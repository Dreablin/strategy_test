"""Tests for World grid, grass zone, and building occupancy."""

import pytest

from game.config import GRID_SIZE, town_hall_footprint_tiles
from game.world import World


def _rect_fully_unoccupied(world: World, gx: int, gy: int, w: int, h: int) -> bool:
    return all(
        not world.is_occupied(tx, ty) for tx in range(gx, gx + w) for ty in range(gy, gy + h)
    )


def test_grid_dimensions_match_config() -> None:
    world = World()
    assert world.width == GRID_SIZE
    assert world.height == GRID_SIZE


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


def test_stone_generation_six_centers_one_on_th_chebyshev_ring_twenty() -> None:
    world = World()
    assert len(world._stone_centers) == 6  # noqa: SLF001
    town_hall_tiles = town_hall_footprint_tiles()
    ring_twenty = [
        (cx, cy)
        for cx, cy in world._stone_centers  # noqa: SLF001
        if min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in town_hall_tiles) == 20
    ]
    assert len(ring_twenty) >= 1
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
        assert 0 <= stone.variant <= 4
        assert not world.is_tree_blocking(gx, gy)


def test_near_town_hall_ring_cluster_places_stones_inside_map_clearing() -> None:
    """Ring-20 center lies in build-clearing Chebyshev zone; stones must still spawn (F-STONE)."""
    world = World(world_seed=0)
    th = town_hall_footprint_tiles()

    def min_th(x: int, y: int) -> int:
        return min(max(abs(x - tx), abs(y - ty)) for tx, ty in th)

    near_ring = [(x, y) for (x, y), _ in world.iter_stones() if 16 <= min_th(x, y) <= 24]
    assert near_ring, "expected at least one stone on/near the TH distance-20 ring cluster"


def test_stone_generation_is_reproducible_with_explicit_world_seed() -> None:
    seed = 9_001_283
    a = World(world_seed=seed)
    b = World(world_seed=seed)
    a_tiles = sorted((pos, stone.units) for pos, stone in a.iter_stones())
    b_tiles = sorted((pos, stone.units) for pos, stone in b.iter_stones())
    assert a_tiles == b_tiles


def test_tree_generation_ten_grove_centers_including_priority_th_rings() -> None:
    world = World(world_seed=2)
    centers = world._tree_centers  # noqa: SLF001
    assert len(centers) == 10
    town_hall_tiles = town_hall_footprint_tiles()

    def min_th(cx: int, cy: int) -> int:
        return min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in town_hall_tiles)

    assert min_th(*centers[0]) == 12
    assert min_th(*centers[1]) == 20
    assert max(abs(centers[0][0] - centers[1][0]), abs(centers[0][1] - centers[1][1])) >= 17

    for cx, cy in centers:
        assert world.is_in_grass(cx, cy)
        assert not world.is_stone_blocking(cx, cy)
        assert min_th(cx, cy) >= 12


def test_tree_generation_is_reproducible_with_explicit_world_seed() -> None:
    seed = 9_001_283
    a = World(world_seed=seed)
    b = World(world_seed=seed)
    a_trees = sorted((pos, tree.stage) for pos, tree in a.iter_alive_trees())
    b_trees = sorted((pos, tree.stage) for pos, tree in b.iter_alive_trees())
    assert a_trees == b_trees


def test_scatter_tree_count_matches_two_percent_floor() -> None:
    world = World()
    budget = int(GRID_SIZE * GRID_SIZE * 0.02)
    assert world._scatter_trees_placed == budget  # noqa: SLF001
