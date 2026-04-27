"""Failing world-tree integration tests for Phase 10 (T65)."""

from game.trees import Tree
from game.world import World


def test_world_exposes_tree_by_tile() -> None:
    world = World()
    tree = world.tree_at(0, 0)
    assert tree is None or isinstance(tree, Tree)


def test_edge_bias_keeps_center_safe_clearing() -> None:
    world = World()
    cx, cy = world.width // 2, world.height // 2
    for gy in range(cy - 3, cy + 4):
        for gx in range(cx - 3, cx + 4):
            assert world.tree_at(gx, gy) is None
            assert not world.is_tree_blocking(gx, gy)


def test_tree_blocking_true_for_alive_false_when_removed() -> None:
    world = World()
    found: tuple[int, int] | None = None
    for gy in range(world.height):
        for gx in range(world.width):
            if world.tree_at(gx, gy) is not None:
                found = (gx, gy)
                break
        if found is not None:
            break
    assert found is not None
    gx, gy = found

    assert world.is_tree_blocking(gx, gy)
    world.remove_tree(gx, gy)
    assert not world.is_tree_blocking(gx, gy)
    assert world.tree_at(gx, gy) is None

