"""Playable isometric grid with occupancy, tree entities, and reservations."""

from __future__ import annotations

from collections import deque
import random

from game.config import GRID_SIZE
from game.stones import Stone
from game.trees import Tree, stage_from_tile_seed

_TREE_EDGE_BAND = 8
_STONE_CENTER_COUNT = 3
_STONE_MIN_DISTANCE_FROM_TOWN_HALL = 12
_NEIGHBORS_4: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
)


class World:
    """Square `GRID_SIZE`×`GRID_SIZE` grass field with occupancy and trees."""

    __slots__ = (
        "_occupied",
        "_occupied_tiles",
        "_trees",
        "_tree_tiles",
        "_stones",
        "_stone_tiles",
        "_tree_reservations",
        "_stone_reservations",
        "_stone_centers",
    )

    def __init__(self) -> None:
        self._occupied: list[list[bool]] = [
            [False] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        self._occupied_tiles: set[tuple[int, int]] = set()
        self._trees: dict[tuple[int, int], Tree] = {}
        self._tree_tiles: set[tuple[int, int]] = set()
        self._stones: dict[tuple[int, int], Stone] = {}
        self._stone_tiles: set[tuple[int, int]] = set()
        self._tree_reservations: dict[tuple[int, int], object] = {}
        self._stone_reservations: dict[tuple[int, int], object] = {}
        self._stone_centers: list[tuple[int, int]] = []
        self._init_stones()
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

    def occupied_tiles(self) -> set[tuple[int, int]]:
        return set(self._occupied_tiles)

    def tree_tiles(self) -> set[tuple[int, int]]:
        # Keep cached set resilient to direct test fixtures mutating `_trees`.
        self._tree_tiles = {(gx, gy) for (gx, gy), tree in self._trees.items() if tree.alive}
        return set(self._tree_tiles)

    def stone_tiles(self) -> set[tuple[int, int]]:
        # Keep cached set resilient to direct test fixtures mutating `_stones`.
        self._stone_tiles = set(self._stones.keys())
        return set(self._stone_tiles)

    def blocked_tiles(self) -> set[tuple[int, int]]:
        return self.occupied_tiles() | self.tree_tiles() | self.stone_tiles()

    def is_tree_blocking(self, gx: int, gy: int) -> bool:
        return self.tree_at(gx, gy) is not None

    def remove_tree(self, gx: int, gy: int) -> None:
        tree = self._trees.get((gx, gy))
        if tree is None:
            return
        tree.remove()
        self._trees.pop((gx, gy), None)
        self._tree_tiles.discard((gx, gy))
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
        to_release_stone = [tile for tile, owner in self._stone_reservations.items() if owner is worker]
        for tile in to_release_stone:
            self._stone_reservations.pop(tile, None)

    def stone_at(self, gx: int, gy: int) -> Stone | None:
        if not self.is_in_grass(gx, gy):
            return None
        return self._stones.get((gx, gy))

    def is_stone_blocking(self, gx: int, gy: int) -> bool:
        return self.stone_at(gx, gy) is not None

    def iter_stones(self) -> list[tuple[tuple[int, int], Stone]]:
        return list(self._stones.items())

    def harvest_stone(self, gx: int, gy: int) -> Stone | None:
        stone = self._stones.get((gx, gy))
        if stone is None:
            return None
        stone.harvest()
        if stone.is_depleted:
            self._stones.pop((gx, gy), None)
            self._stone_tiles.discard((gx, gy))
            self._stone_reservations.pop((gx, gy), None)
        return stone

    def reserve_stone(self, gx: int, gy: int, worker: object) -> bool:
        tile = (gx, gy)
        if self.stone_at(gx, gy) is None:
            return False
        existing = self._stone_reservations.get(tile)
        if existing is None:
            self._stone_reservations[tile] = worker
            return True
        return existing is worker

    def release_stone(self, gx: int, gy: int) -> None:
        self._stone_reservations.pop((gx, gy), None)

    def is_stone_reserved(self, gx: int, gy: int) -> bool:
        return (gx, gy) in self._stone_reservations

    def mark_occupied(self, gx: int, gy: int, w: int, h: int) -> None:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self.is_in_grass(tx, ty):
                    self._occupied[ty][tx] = True
                    self._occupied_tiles.add((tx, ty))

    def free(self, gx: int, gy: int, w: int, h: int) -> None:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self.is_in_grass(tx, ty):
                    self._occupied[ty][tx] = False
                    self._occupied_tiles.discard((tx, ty))

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
                if self.is_stone_blocking(gx, gy):
                    continue
                seed = gx * 92821 + gy * 68917 + GRID_SIZE * 37
                noise = self._tile_noise(gx, gy)
                # Dense near border, still populated deeper into 5-8 edge rows.
                # edge_dist=0 -> 0.78, edge_dist=7 -> 0.42
                threshold = 0.78 - (0.36 * (edge_dist / (_TREE_EDGE_BAND - 1)))
                if noise < threshold:
                    tile = (gx, gy)
                    self._trees[tile] = Tree(stage=stage_from_tile_seed(seed))
                    self._tree_tiles.add(tile)

    def _init_stones(self) -> None:
        rng = random.Random(GRID_SIZE * 104_729 + 17)
        self._stone_centers = []
        mid = GRID_SIZE // 2
        center_clear_radius = max(8, GRID_SIZE // 4)
        protected = {(x, y) for y in range(16, 19) for x in range(16, 19)}
        candidates = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
        rng.shuffle(candidates)
        for cx, cy in candidates:
            if len(self._stone_centers) >= _STONE_CENTER_COUNT:
                break
            if max(abs(cx - mid), abs(cy - mid)) <= center_clear_radius:
                continue
            if any(
                max(abs(cx - tx), abs(cy - ty)) < _STONE_MIN_DISTANCE_FROM_TOWN_HALL
                for tx, ty in protected
            ):
                continue
            if not self.is_in_grass(cx, cy):
                continue
            self._stone_centers.append((cx, cy))

        for cx, cy in self._stone_centers:
            radius = rng.randint(3, 6)
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if not self.is_in_grass(x, y):
                        continue
                    if max(abs(x - mid), abs(y - mid)) <= center_clear_radius:
                        continue
                    if max(abs(x - cx), abs(y - cy)) > radius:
                        continue
                    if self.is_tree_blocking(x, y):
                        continue
                    if (x, y) in self._stones:
                        continue
                    tile = (x, y)
                    self._stones[tile] = Stone()
                    self._stone_tiles.add(tile)

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
    skip_targets: set[tuple[int, int]] | None = None,
) -> tuple[int, int] | None:
    """Return nearest alive tree tile reachable from `from_tile` over walkable tiles."""
    sx, sy = from_tile
    if not world.is_in_grass(sx, sy):
        return None

    skip = skip_targets or set()
    start_tree = world.tree_at(sx, sy)
    if (
        start_tree is not None
        and from_tile not in skip
        and (not skip_reserved or not world.is_tree_reserved(sx, sy))
    ):
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
        for dx, dy in _NEIGHBORS_4:
            nx, ny = cx + dx, cy + dy
            nxt = (nx, ny)
            if not world.is_in_grass(nx, ny):
                continue
            if world.tree_at(nx, ny) is not None:
                if nxt in skip:
                    continue
                if skip_reserved and world.is_tree_reserved(nx, ny):
                    continue
                return nxt
            if nxt in seen or not is_walkable(nxt):
                continue
            seen.add(nxt)
            q.append(nxt)
    return None


def find_nearest_free_stone(
    world: World,
    from_tile: tuple[int, int],
    *,
    blocked: set[tuple[int, int]],
    skip_reserved: bool = True,
    skip_targets: set[tuple[int, int]] | None = None,
) -> tuple[int, int] | None:
    """Return nearest stone tile reachable from `from_tile` over walkable tiles."""
    sx, sy = from_tile
    if not world.is_in_grass(sx, sy):
        return None

    skip = skip_targets or set()
    start_stone = world.stone_at(sx, sy)
    if (
        start_stone is not None
        and from_tile not in skip
        and (not skip_reserved or not world.is_stone_reserved(sx, sy))
    ):
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
        if world.is_stone_blocking(tx, ty):
            return False
        return True

    if not is_walkable(from_tile):
        return None

    q: deque[tuple[int, int]] = deque([from_tile])
    seen: set[tuple[int, int]] = {from_tile}
    while q:
        cx, cy = q.popleft()
        for dx, dy in _NEIGHBORS_4:
            nx, ny = cx + dx, cy + dy
            nxt = (nx, ny)
            if not world.is_in_grass(nx, ny):
                continue
            if world.stone_at(nx, ny) is not None:
                if nxt in skip:
                    continue
                if skip_reserved and world.is_stone_reserved(nx, ny):
                    continue
                return nxt
            if nxt in seen or not is_walkable(nxt):
                continue
            seen.add(nxt)
            q.append(nxt)
    return None
