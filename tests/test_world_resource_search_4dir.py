"""Failing tests for 4-direction resource search expansion in world helpers (T133)."""

from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World, find_nearest_free_stone, find_nearest_free_tree


def _empty_world() -> World:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    return world


def test_find_nearest_free_tree_does_not_reach_diagonal_only_target() -> None:
    world = _empty_world()
    world._trees[(5, 5)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    blocked = {(5, 4), (4, 5), (6, 5), (5, 6)}

    nearest = find_nearest_free_tree(world, (4, 4), blocked=blocked, skip_reserved=True)

    assert nearest is None


def test_find_nearest_free_tree_returns_target_with_orthogonal_access() -> None:
    world = _empty_world()
    world._trees[(5, 5)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    nearest = find_nearest_free_tree(world, (4, 4), blocked=set(), skip_reserved=True)

    assert nearest == (5, 5)


def test_find_nearest_free_stone_does_not_reach_diagonal_only_target() -> None:
    world = _empty_world()
    world._stones[(5, 5)] = Stone(units=2)  # noqa: SLF001
    blocked = {(5, 4), (4, 5), (6, 5), (5, 6)}

    nearest = find_nearest_free_stone(world, (4, 4), blocked=blocked, skip_reserved=True)

    assert nearest is None


def test_find_nearest_free_stone_returns_target_with_orthogonal_access() -> None:
    world = _empty_world()
    world._stones[(5, 5)] = Stone(units=2)  # noqa: SLF001

    nearest = find_nearest_free_stone(world, (4, 4), blocked=set(), skip_reserved=True)

    assert nearest == (5, 5)
