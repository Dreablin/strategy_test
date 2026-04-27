"""Playable isometric grid with occupancy, tree entities, and reservations."""

from __future__ import annotations

from collections import deque

from game.config import GRID_SIZE
from game.trees import Tree, stage_from_tile_seed

_TREE_EDGE_BAND = 8
_NEIGHBORS_8: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
)


class World:
    """Square `GRID_SIZE`×`GRID_SIZE` grass field with occupancy and trees."""

    __slots__ = ("_occupied", "_trees", "_tree_reservations")

    def __init__(self) -> None:
        self._occupied: list[list[bool]] = [
            [False] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        self._trees: dict[tuple[int, int], Tree] = {}
        self._tree_reservations: dict[tuple[int, int], object] = {}
        self._init_trees()

    @property
    def width(self) -> int:
        return GRID_SIZE

    @property
    def height(self) -> int:
        return GRID_SIZE

    def is_in_grass(self, gx: int, gy: int) -> bool:
        return 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE

    def is_occupied(self, gx: int, gy: int) -> bool:
        if not self.is_in_grass(gx, gy):
            return False
        return self._occupied[gy][gx]

    def tree_at(self, gx: int, gy: int) -> Tree | None:
        if not self.is_in_grass(gx, gy):
            return None
        tree = self._trees.get((gx, gy))
        if tree is None or not tree.alive:
            return None
        return tree

    def iter_alive_trees(self) -> list[tuple[tuple[int, int], Tree]]:
        return [((gx, gy), tree) for (gx, gy), tree in self._trees.items() if tree.alive]

    def is_tree_blocking(self, gx: int, gy: int) -> bool:
        return self.tree_at(gx, gy) is not None

    def remove_tree(self, gx: int, gy: int) -> None:
        tree = self._trees.get((gx, gy))
        if tree is None:
            return
        tree.remove()
        self._trees.pop((gx, gy), None)
        self._tree_reservations.pop((gx, gy), None)

    def reserve_tree(self, gx: int, gy: int, worker: object) -> bool:
        tile = (gx, gy)
        if self.tree_at(gx, gy) is None:
            return False
        existing = self._tree_reservations.get(tile)
        if existing is None:
            self._tree_reservations[tile] = worker
            return True
        return existing is worker

    def release_tree(self, gx: int, gy: int) -> None:
        self._tree_reservations.pop((gx, gy), None)

    def is_tree_reserved(self, gx: int, gy: int) -> bool:
        return (gx, gy) in self._tree_reservations

    def release_reservations_for(self, worker: object) -> None:
        to_release = [tile for tile, owner in self._tree_reservations.items() if owner is worker]
        for tile in to_release:
            self._tree_reservations.pop(tile, None)

    def mark_occupied(self, gx: int, gy: int, w: int, h: int) -> None:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self.is_in_grass(tx, ty):
                    self._occupied[ty][tx] = True

    def free(self, gx: int, gy: int, w: int, h: int) -> None:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self.is_in_grass(tx, ty):
                    self._occupied[ty][tx] = False

    def _init_trees(self) -> None:
        cx = GRID_SIZE // 2
        cy = GRID_SIZE // 2
        center_clear_radius = max(8, GRID_SIZE // 4)
        for gy in range(GRID_SIZE):
            for gx in range(GRID_SIZE):
                if max(abs(gx - cx), abs(gy - cy)) <= center_clear_radius:
                    continue
                edge_dist = min(gx, gy, GRID_SIZE - 1 - gx, GRID_SIZE - 1 - gy)
                if edge_dist >= _TREE_EDGE_BAND:
                    continue
                seed = gx * 92821 + gy * 68917 + GRID_SIZE * 37
                noise = self._tile_noise(gx, gy)
                # Dense near border, still populated deeper into 5-8 edge rows.
                # edge_dist=0 -> 0.78, edge_dist=7 -> 0.42
                threshold = 0.78 - (0.36 * (edge_dist / (_TREE_EDGE_BAND - 1)))
                if noise < threshold:
                    self._trees[(gx, gy)] = Tree(stage=stage_from_tile_seed(seed))

    @staticmethod
    def _tile_noise(gx: int, gy: int) -> float:
        """Stable pseudo-random [0,1) value per tile with low visible patterns."""
        n = (gx * 0x9E3779B1) ^ (gy * 0x85EBCA77) ^ 0xC2B2AE3D
        n ^= n >> 16
        n = (n * 0x7FEB352D) & 0xFFFFFFFF
        n ^= n >> 15
        n = (n * 0x846CA68B) & 0xFFFFFFFF
        n ^= n >> 16
        return n / 0x100000000


def find_nearest_free_tree(
    world: World,
    from_tile: tuple[int, int],
    *,
    blocked: set[tuple[int, int]],
    skip_reserved: bool = True,
) -> tuple[int, int] | None:
    """Return nearest alive tree tile reachable from `from_tile` over walkable tiles."""
    sx, sy = from_tile
    if not world.is_in_grass(sx, sy):
        return None

    start_tree = world.tree_at(sx, sy)
    if start_tree is not None and (not skip_reserved or not world.is_tree_reserved(sx, sy)):
        return from_tile

    def is_walkable(tile: tuple[int, int]) -> bool:
        tx, ty = tile
        if not world.is_in_grass(tx, ty):
            return False
        if tile in blocked and tile != from_tile:
            return False
        if world.is_occupied(tx, ty):
            return False
        if world.is_tree_blocking(tx, ty):
            return False
        return True

    if not is_walkable(from_tile):
        return None

    q: deque[tuple[int, int]] = deque([from_tile])
    seen: set[tuple[int, int]] = {from_tile}
    while q:
        cx, cy = q.popleft()
        for dx, dy in _NEIGHBORS_8:
            nx, ny = cx + dx, cy + dy
            nxt = (nx, ny)
            if not world.is_in_grass(nx, ny):
                continue
            if world.tree_at(nx, ny) is not None:
                if skip_reserved and world.is_tree_reserved(nx, ny):
                    continue
                return nxt
            if nxt in seen or not is_walkable(nxt):
                continue
            seen.add(nxt)
            q.append(nxt)
    return None
