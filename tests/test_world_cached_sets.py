"""Failing tests for cached world tile-set APIs (T126)."""

from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World


def test_world_exposes_cached_set_getters_with_expected_types() -> None:
    world = World()
    assert isinstance(world.occupied_tiles(), set)
    assert isinstance(world.tree_tiles(), set)
    assert isinstance(world.stone_tiles(), set)
    assert isinstance(world.gold_tiles(), set)
    assert isinstance(world.gold_blocking_tiles(), set)
    assert isinstance(world.gold_buildable_tiles(), set)
    assert isinstance(world.iron_tiles(), set)
    assert isinstance(world.iron_blocking_tiles(), set)
    assert isinstance(world.iron_buildable_tiles(), set)
    assert isinstance(world.blocked_tiles(), set)


def test_occupied_tiles_roundtrip_mark_and_free() -> None:
    world = World()
    assert world.occupied_tiles() == set()
    world.mark_occupied(5, 5, 2, 2)
    assert world.occupied_tiles() == {(5, 5), (6, 5), (5, 6), (6, 6)}
    world.free(5, 5, 2, 2)
    assert world.occupied_tiles() == set()


def test_tree_tiles_mirror_tree_lifecycle_and_remove_tree() -> None:
    world = World()
    expected = {(gx, gy) for gy in range(world.height) for gx in range(world.width) if world.tree_at(gx, gy)}
    assert world.tree_tiles() == expected
    tile = next(iter(expected))
    world.remove_tree(*tile)
    expected.remove(tile)
    assert world.tree_tiles() == expected


def test_stone_tiles_mirror_stone_lifecycle_and_deplete_on_harvest() -> None:
    world = World()
    world._stones.clear()  # noqa: SLF001
    world._stones[(9, 9)] = Stone(units=1)  # noqa: SLF001
    assert world.stone_tiles() == {(9, 9)}
    world.harvest_stone(9, 9)
    assert world.stone_tiles() == set()


def test_blocked_tiles_equals_union_after_mutations() -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._trees[(3, 3)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._stones[(4, 4)] = Stone(units=2)  # noqa: SLF001
    world.mark_occupied(5, 5, 1, 1)
    assert world.blocked_tiles() == (
        world.occupied_tiles()
        | world.tree_tiles()
        | world.stone_tiles()
        | world.iron_blocking_tiles()
        | world.gold_blocking_tiles()
    )
    world.remove_tree(3, 3)
    world.harvest_stone(4, 4)
    world.harvest_stone(4, 4)
    world.free(5, 5, 1, 1)
    assert world.blocked_tiles() == (
        world.occupied_tiles()
        | world.tree_tiles()
        | world.stone_tiles()
        | world.iron_blocking_tiles()
        | world.gold_blocking_tiles()
    )


def test_cached_set_getters_return_copies_not_internal_mutable_state() -> None:
    world = World()
    world.mark_occupied(5, 5, 1, 1)
    tiles = world.occupied_tiles()
    tiles.add((9, 9))
    assert (9, 9) not in world.occupied_tiles()


def test_tree_layer_pop_updates_passability_caches() -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._trees[(2, 2)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    assert (2, 2) in world.blocked_tiles()
    world._trees.pop((2, 2), None)
    assert (2, 2) not in world.tree_tiles()
    assert (2, 2) not in world.blocked_tiles()


def test_stone_layer_pop_updates_passability_caches() -> None:
    world = World()
    world._stones.clear()  # noqa: SLF001
    world._stones[(3, 3)] = Stone(units=1)  # noqa: SLF001
    assert (3, 3) in world.blocked_tiles()
    world._stones.pop((3, 3), None)
    assert (3, 3) not in world.stone_tiles()
    assert (3, 3) not in world.blocked_tiles()
