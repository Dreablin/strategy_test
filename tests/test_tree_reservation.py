"""Failing tests for tree reservation behavior (T77)."""

from game.trees import Tree, TreeStage
from game.world import World, find_nearest_free_tree


def test_reserve_tree_allows_only_single_owner() -> None:
    world = World()
    world._trees[(12, 12)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    worker_a = object()
    worker_b = object()

    assert world.reserve_tree(12, 12, worker_a) is True
    assert world.reserve_tree(12, 12, worker_b) is False


def test_release_reservations_for_worker_releases_tile() -> None:
    world = World()
    world._trees[(13, 13)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    worker = object()

    assert world.reserve_tree(13, 13, worker) is True
    world.release_reservations_for(worker)
    assert world.reserve_tree(13, 13, object()) is True


def test_tree_removal_clears_reservation() -> None:
    world = World()
    world._trees[(14, 14)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    worker = object()

    assert world.reserve_tree(14, 14, worker) is True
    world.remove_tree(14, 14)
    assert world.is_tree_reserved(14, 14) is False


def test_find_nearest_free_tree_skips_reserved_tiles() -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._trees[(11, 10)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(12, 10)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    worker = object()
    assert world.reserve_tree(11, 10, worker) is True

    nearest = find_nearest_free_tree(world, (10, 10), blocked=set(), skip_reserved=True)
    assert nearest == (12, 10)
