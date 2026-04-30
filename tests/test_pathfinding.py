"""Failing pathfinding tests for Phase 9 (T56)."""

from game.pathfinding import find_path_bfs
from game.trees import Tree, TreeStage
from game.world import World


def _blocked_from_world(world: World) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(world.height)
        for x in range(world.width)
        if world.is_occupied(x, y)
    }


def _clear_resources(world: World) -> None:
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001


def test_bfs_finds_4dir_path_around_obstacles() -> None:
    world = World(world_seed=2)
    _clear_resources(world)
    start = (20, 20)
    goal = (24, 20)
    blocked = {(22, y) for y in range(19, 24)}
    blocked.remove((22, 21))

    path = find_path_bfs(world, start, goal, blocked)

    assert path is not None
    assert path[0] == start
    assert path[-1] == goal
    # BFS may choose either side opening depending on deterministic order.
    assert any(x == 22 and y not in blocked for x, y in path)
    assert all(tile not in blocked for tile in path)
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))


def test_path_never_steps_on_occupied_footprint_tiles() -> None:
    world = World(world_seed=2)
    _clear_resources(world)
    world.mark_occupied(10, 10, 2, 2)
    blocked = _blocked_from_world(world)
    start = (8, 11)
    goal = (13, 11)

    path = find_path_bfs(world, start, goal, blocked)

    assert path is not None
    assert path[0] == start
    assert path[-1] == goal
    assert all(tile not in blocked for tile in path)


def test_returns_none_when_goal_unreachable() -> None:
    world = World(world_seed=2)
    _clear_resources(world)
    goal = (5, 5)
    blocked = {
        (4, 4),
        (5, 4),
        (6, 4),
        (4, 5),
        (6, 5),
        (4, 6),
        (5, 6),
        (6, 6),
    }

    path = find_path_bfs(world, (1, 1), goal, blocked)

    assert path is None


def test_bfs_avoids_alive_tree_tiles() -> None:
    world = World(world_seed=2)
    _clear_resources(world)
    # Force a tree on the straight-line shortest route.
    world._trees[(12, 10)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    # Goal must be a grass tile without a generated tree (e.g. (14,10) is often occupied).
    path = find_path_bfs(world, (10, 10), (13, 10), blocked=set())
    assert path is not None
    assert (12, 10) not in path


def test_tree_removed_tile_becomes_walkable_for_path() -> None:
    world = World(world_seed=2)
    _clear_resources(world)
    world._trees[(12, 10)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    blocked = {(x, 9) for x in range(world.width)} | {(x, 11) for x in range(world.width)}
    path_with_tree = find_path_bfs(world, (10, 10), (13, 10), blocked=blocked)
    assert path_with_tree is None

    world.remove_tree(12, 10)
    path_after_remove = find_path_bfs(world, (10, 10), (13, 10), blocked=blocked)
    assert path_after_remove is not None
    assert (12, 10) in path_after_remove


def test_bfs_avoids_alive_stone_tiles() -> None:
    from game.stones import Stone

    world = World(world_seed=2)
    _clear_resources(world)
    world._stones[(12, 10)] = Stone()  # noqa: SLF001
    path = find_path_bfs(world, (10, 10), (13, 10), blocked=set())
    assert path is not None
    assert (12, 10) not in path
