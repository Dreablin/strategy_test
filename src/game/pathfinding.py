"""Deterministic 8-direction BFS pathfinding over world grass tiles."""

from __future__ import annotations

from collections import deque

from game.world import World

_NEIGHBORS_8: tuple[tuple[int, int], ...] = (
    (0, -1),   # N
    (1, -1),   # NE
    (1, 0),    # E
    (1, 1),    # SE
    (0, 1),    # S
    (-1, 1),   # SW
    (-1, 0),   # W
    (-1, -1),  # NW
)


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int] | None],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


def find_path_bfs(
    world: World,
    start: tuple[int, int],
    goal: tuple[int, int],
    blocked: set[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    """Return inclusive `[start..goal]` path, or `None` when unreachable."""
    def is_walkable(tile: tuple[int, int]) -> bool:
        x, y = tile
        return world.is_in_grass(x, y) and tile not in blocked and not world.is_tree_blocking(x, y)

    if not world.is_in_grass(*start) or not world.is_in_grass(*goal):
        return None
    if start != goal and (start in blocked or goal in blocked):
        return None
    if start != goal and (world.is_tree_blocking(*start) or world.is_tree_blocking(*goal)):
        return None
    if start == goal:
        return [start]

    frontier: deque[tuple[int, int]] = deque([start])
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while frontier:
        cx, cy = frontier.popleft()
        if (cx, cy) == goal:
            return _reconstruct_path(came_from, goal)

        for dx, dy in _NEIGHBORS_8:
            nx, ny = cx + dx, cy + dy
            nxt = (nx, ny)

            if not is_walkable(nxt):
                continue
            if nxt in came_from:
                continue

            # For diagonal moves, disallow corner cutting only when both
            # adjacent orthogonals are blocked/unwalkable.
            if dx != 0 and dy != 0:
                side_a = (cx + dx, cy)
                side_b = (cx, cy + dy)
                a_walkable = is_walkable(side_a)
                b_walkable = is_walkable(side_b)
                if not (a_walkable or b_walkable):
                    continue

            came_from[nxt] = (cx, cy)
            frontier.append(nxt)

    return None
