"""Bounded gather-target search (Chebyshev disk around the staffed camp)."""

from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World, find_nearest_free_stone, find_nearest_free_tree


def _empty_world() -> World:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    return world


def test_find_nearest_free_tree_respects_search_radius() -> None:
    world = _empty_world()
    anchor = (25, 25)
    # On the boundary of Chebyshev radius 20 from anchor (25, 25).
    world._trees[(45, 25)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    # Just outside the disk — must not be returned when bounded.
    world._trees[(46, 25)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    nearest = find_nearest_free_tree(
        world,
        (25, 25),
        blocked=set(),
        skip_reserved=True,
        search_anchor=anchor,
        max_search_radius=20,
    )
    assert nearest == (45, 25)

    nearest_out = find_nearest_free_tree(
        world,
        (25, 25),
        blocked=set(),
        skip_reserved=True,
        skip_targets={(45, 25)},
        search_anchor=anchor,
        max_search_radius=20,
    )
    assert nearest_out is None


def test_find_nearest_free_tree_unbounded_still_sees_outside_radius() -> None:
    world = _empty_world()
    world._trees[(46, 25)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    nearest = find_nearest_free_tree(world, (25, 25), blocked=set(), skip_reserved=True)
    assert nearest == (46, 25)


def test_find_nearest_free_tree_returns_none_if_start_outside_disk() -> None:
    world = _empty_world()
    world._trees[(45, 25)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    # Chebyshev distance from (4, 4) to (25, 25) is 21 > 20.
    nearest = find_nearest_free_tree(
        world,
        (4, 4),
        blocked=set(),
        skip_reserved=True,
        search_anchor=(25, 25),
        max_search_radius=20,
    )
    assert nearest is None


def test_find_nearest_free_stone_respects_search_radius() -> None:
    world = _empty_world()
    anchor = (25, 25)
    world._stones[(45, 25)] = Stone(units=5)  # noqa: SLF001
    world._stones[(46, 25)] = Stone(units=5)  # noqa: SLF001

    nearest = find_nearest_free_stone(
        world,
        (25, 25),
        blocked=set(),
        skip_reserved=True,
        search_anchor=anchor,
        max_search_radius=20,
    )
    assert nearest == (45, 25)

    nearest_out = find_nearest_free_stone(
        world,
        (25, 25),
        blocked=set(),
        skip_reserved=True,
        skip_targets={(45, 25)},
        search_anchor=anchor,
        max_search_radius=20,
    )
    assert nearest_out is None
