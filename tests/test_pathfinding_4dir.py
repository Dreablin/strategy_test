"""Failing tests pinning 4-direction BFS requirements (T131)."""

from game.pathfinding import find_path_bfs
from game.world import World


def test_4dir_path_length_equals_manhattan_plus_one_on_empty_grid() -> None:
    world = World()
    start = (0, 0)
    goal = (3, 3)
    path = find_path_bfs(world, start, goal, blocked=set())

    assert path is not None
    assert len(path) == 7  # Manhattan(0,0 -> 3,3) + 1


def test_4dir_path_contains_only_orthogonal_steps() -> None:
    world = World()
    path = find_path_bfs(world, (0, 0), (3, 3), blocked=set())

    assert path is not None
    for a, b in zip(path, path[1:]):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        assert dx + dy == 1


def test_diagonal_wall_pattern_is_unreachable_until_one_blocker_removed() -> None:
    world = World()
    blocked = {(1, 0), (0, 1)}

    path = find_path_bfs(world, (0, 0), (1, 1), blocked=blocked)
    assert path is None

    blocked.remove((1, 0))
    path_after = find_path_bfs(world, (0, 0), (1, 1), blocked=blocked)
    assert path_after is not None


def test_bfs_is_deterministic_for_identical_inputs() -> None:
    world = World()
    blocked = {(2, 1), (2, 2), (2, 3)}
    a = find_path_bfs(world, (0, 0), (4, 4), blocked=blocked)
    b = find_path_bfs(world, (0, 0), (4, 4), blocked=blocked)
    assert a == b


def test_4dir_reachability_and_start_equals_goal() -> None:
    world = World()
    assert find_path_bfs(world, (2, 2), (2, 2), blocked=set()) == [(2, 2)]

    path = find_path_bfs(world, (1, 1), (1, 4), blocked=set())
    assert path is not None
    assert path[0] == (1, 1)
    assert path[-1] == (1, 4)
