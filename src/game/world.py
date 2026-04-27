"""Playable isometric grid with occupancy, tree entities, and reservations."""

from __future__ import annotations

from collections import deque
import random
from typing import Any, cast

from game.config import GRID_SIZE
from game.stones import Stone
from game.trees import Tree, stage_from_tile_seed

_STONE_CENTER_COUNT = 3
_TREE_GROVE_COUNT = 3
_STONE_MIN_DISTANCE_FROM_TOWN_HALL = 12
_TREE_GROVE_RADIUS_MIN = 3
_TREE_GROVE_RADIUS_MAX = 6
_TREE_GROVE_FILL_PROBABILITY = 0.8
_NEIGHBORS_4: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
)

_POP_MISSING = object()


def _within_gather_search_radius(
    tile: tuple[int, int],
    search_anchor: tuple[int, int],
    max_search_radius: int,
) -> bool:
    """True iff `tile` lies inside the Chebyshev ball around `search_anchor`."""
    tx, ty = tile
    ax, ay = search_anchor
    return max(abs(tx - ax), abs(ty - ay)) <= max_search_radius


class _TreeLayerDict(dict[tuple[int, int], Tree]):
    """`_trees` storage that keeps `_tree_tiles` / `_blocked_tiles` in sync on mutation."""

    __slots__ = ("_owner",)

    def __init__(self, owner: World) -> None:
        super().__init__()
        self._owner = owner

    def __setitem__(self, key: tuple[int, int], value: Tree) -> None:
        super().__setitem__(key, value)
        if value.alive:
            self._owner._tree_tiles.add(key)
            self._owner._blocked_tiles.add(key)

    def __delitem__(self, key: tuple[int, int]) -> None:
        super().__delitem__(key)
        self._owner._tree_tiles.discard(key)
        self._owner._blocked_tiles.discard(key)

    def pop(self, key: tuple[int, int], default: Any = _POP_MISSING) -> Tree:
        """Like ``dict.pop`` but always runs :meth:`__delitem__` so passability caches stay valid."""
        if key not in self:
            if default is _POP_MISSING:
                raise KeyError(key)
            return cast("Tree", default)
        value = super().__getitem__(key)
        del self[key]
        return value

    def clear(self) -> None:
        super().clear()
        o = self._owner
        o._tree_tiles.clear()
        o._blocked_tiles = set(o._occupied_tiles) | o._stone_tiles


class _StoneLayerDict(dict[tuple[int, int], Stone]):
    """`_stones` storage that keeps `_stone_tiles` / `_blocked_tiles` in sync on mutation."""

    __slots__ = ("_owner",)

    def __init__(self, owner: World) -> None:
        super().__init__()
        self._owner = owner

    def __setitem__(self, key: tuple[int, int], value: Stone) -> None:
        super().__setitem__(key, value)
        self._owner._stone_tiles.add(key)
        self._owner._blocked_tiles.add(key)

    def __delitem__(self, key: tuple[int, int]) -> None:
        super().__delitem__(key)
        self._owner._stone_tiles.discard(key)
        self._owner._blocked_tiles.discard(key)

    def pop(self, key: tuple[int, int], default: Any = _POP_MISSING) -> Stone:
        if key not in self:
            if default is _POP_MISSING:
                raise KeyError(key)
            return cast("Stone", default)
        value = super().__getitem__(key)
        del self[key]
        return value

    def clear(self) -> None:
        super().clear()
        o = self._owner
        o._stone_tiles.clear()
        o._blocked_tiles = set(o._occupied_tiles) | o._tree_tiles


class World:
    """Square `GRID_SIZE`×`GRID_SIZE` grass field with occupancy and trees."""

    __slots__ = (
        "_occupied",
        "_occupied_tiles",
        "_trees",
        "_tree_tiles",
        "_stones",
        "_stone_tiles",
        "_blocked_tiles",
        "_tree_reservations",
        "_stone_reservations",
        "_stone_centers",
        "_tree_centers",
    )

    def __init__(self) -> None:
        self._occupied: list[list[bool]] = [
            [False] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        self._occupied_tiles: set[tuple[int, int]] = set()
        self._trees = _TreeLayerDict(self)
        self._tree_tiles: set[tuple[int, int]] = set()
        self._stones = _StoneLayerDict(self)
        self._stone_tiles: set[tuple[int, int]] = set()
        self._blocked_tiles: set[tuple[int, int]] = set()
        self._tree_reservations: dict[tuple[int, int], object] = {}
        self._stone_reservations: dict[tuple[int, int], object] = {}
        self._stone_centers: list[tuple[int, int]] = []
        self._tree_centers: list[tuple[int, int]] = []
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
        """Alive tree tiles; kept in sync via `_TreeLayerDict` mutations."""
        return set(self._tree_tiles)

    def stone_tiles(self) -> set[tuple[int, int]]:
        """Stone tiles; maintained incrementally."""
        return set(self._stone_tiles)

    def blocked_tiles(self) -> set[tuple[int, int]]:
        """Union of building footprints, alive trees, and stones — one set copy."""
        return set(self._blocked_tiles)

    def refresh_passability_tile_caches(self) -> None:
        """Rebuild derived tile sets from `_trees`, `_stones`, and `_occupied_tiles`.

        Normal gameplay keeps caches in sync via `_TreeLayerDict` / `_StoneLayerDict`,
        `remove_tree`, `harvest_stone`, `mark_occupied`, and `free`. Call this only
        after **test** code that replaces `_trees` or `_stones` with a plain `dict`
        (e.g. ``world._stones = {...}``), which bypasses the tracking wrappers.
        """
        self._tree_tiles = {(gx, gy) for (gx, gy), tree in self._trees.items() if tree.alive}
        self._stone_tiles = set(self._stones.keys())
        self._blocked_tiles = set(self._occupied_tiles) | self._tree_tiles | self._stone_tiles

    def is_tree_blocking(self, gx: int, gy: int) -> bool:
        return self.tree_at(gx, gy) is not None

    def remove_tree(self, gx: int, gy: int) -> None:
        tree = self._trees.get((gx, gy))
        if tree is None:
            return
        tree.remove()
        tile = (gx, gy)
        self._trees.pop(tile, None)
        self._tree_reservations.pop(tile, None)

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
            tile = (gx, gy)
            self._stones.pop(tile, None)
            self._stone_reservations.pop(tile, None)
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
                    tile = (tx, ty)
                    self._occupied_tiles.add(tile)
                    self._blocked_tiles.add(tile)

    def free(self, gx: int, gy: int, w: int, h: int) -> None:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self.is_in_grass(tx, ty):
                    self._occupied[ty][tx] = False
                    tile = (tx, ty)
                    self._occupied_tiles.discard(tile)
                    self._blocked_tiles.discard(tile)

    def _init_trees(self) -> None:
        rng = random.Random(GRID_SIZE * 91_237 + 43)
        self._tree_centers = _pick_far_cluster_centers(
            self, _TREE_GROVE_COUNT, rng, forbid_stone_center=True
        )
        mid = GRID_SIZE // 2
        center_clear_radius = max(8, GRID_SIZE // 4)
        for cx, cy in self._tree_centers:
            radius = rng.randint(_TREE_GROVE_RADIUS_MIN, _TREE_GROVE_RADIUS_MAX)
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if not self.is_in_grass(x, y):
                        continue
                    if max(abs(x - mid), abs(y - mid)) <= center_clear_radius:
                        continue
                    if max(abs(x - cx), abs(y - cy)) > radius:
                        continue
                    if self.is_stone_blocking(x, y):
                        continue
                    if (x, y) in self._trees:
                        continue
                    if rng.random() >= _TREE_GROVE_FILL_PROBABILITY:
                        continue
                    seed = x * 92821 + y * 68917 + GRID_SIZE * 37
                    self._trees[(x, y)] = Tree(stage=stage_from_tile_seed(seed))

    def _init_stones(self) -> None:
        rng = random.Random(GRID_SIZE * 104_729 + 17)
        self._stone_centers = _pick_far_cluster_centers(
            self, _STONE_CENTER_COUNT, rng, forbid_stone_center=False
        )
        mid = GRID_SIZE // 2
        center_clear_radius = max(8, GRID_SIZE // 4)

        for cx, cy in self._stone_centers:
            radius = rng.randint(1, 4)
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


def _town_hall_footprint_tiles() -> set[tuple[int, int]]:
    """Town Hall is placed at (16, 16) with footprint 3×3 in `main.py`."""
    return {(x, y) for y in range(16, 19) for x in range(16, 19)}


def _pick_far_cluster_centers(
    world: World,
    count: int,
    rng: random.Random,
    *,
    forbid_stone_center: bool,
) -> list[tuple[int, int]]:
    """Pick up to `count` grass tiles outside the build clearing, Chebyshev ≥ TH distance."""
    mid = GRID_SIZE // 2
    center_clear_radius = max(8, GRID_SIZE // 4)
    protected = _town_hall_footprint_tiles()
    candidates = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
    rng.shuffle(candidates)
    centers: list[tuple[int, int]] = []
    for cx, cy in candidates:
        if len(centers) >= count:
            break
        if max(abs(cx - mid), abs(cy - mid)) <= center_clear_radius:
            continue
        if any(
            max(abs(cx - tx), abs(cy - ty)) < _STONE_MIN_DISTANCE_FROM_TOWN_HALL
            for tx, ty in protected
        ):
            continue
        if not world.is_in_grass(cx, cy):
            continue
        if forbid_stone_center and world.is_stone_blocking(cx, cy):
            continue
        centers.append((cx, cy))
    return centers


def find_nearest_free_tree(
    world: World,
    from_tile: tuple[int, int],
    *,
    blocked: set[tuple[int, int]],
    skip_reserved: bool = True,
    skip_targets: set[tuple[int, int]] | None = None,
    search_anchor: tuple[int, int] | None = None,
    max_search_radius: int | None = None,
) -> tuple[int, int] | None:
    """Return nearest alive tree tile reachable from `from_tile` over walkable tiles.

    When ``search_anchor`` and ``max_search_radius`` are both set, BFS never
    leaves the Chebyshev disk of radius ``max_search_radius`` around
    ``search_anchor`` (typically the staffed camp centre). This caps worst-case
    work at O(r²) instead of the full map.
    """
    sx, sy = from_tile
    if not world.is_in_grass(sx, sy):
        return None

    anchor = search_anchor
    radius = max_search_radius
    if anchor is not None and radius is not None:
        if not _within_gather_search_radius(from_tile, anchor, radius):
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
            if anchor is not None and radius is not None and not _within_gather_search_radius(nxt, anchor, radius):
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
    search_anchor: tuple[int, int] | None = None,
    max_search_radius: int | None = None,
) -> tuple[int, int] | None:
    """Return nearest stone tile reachable from `from_tile` over walkable tiles.

    Optional ``search_anchor`` / ``max_search_radius`` bound the search to a
    Chebyshev disk (same contract as :func:`find_nearest_free_tree`).
    """
    sx, sy = from_tile
    if not world.is_in_grass(sx, sy):
        return None

    anchor = search_anchor
    radius = max_search_radius
    if anchor is not None and radius is not None:
        if not _within_gather_search_radius(from_tile, anchor, radius):
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
            if anchor is not None and radius is not None and not _within_gather_search_radius(nxt, anchor, radius):
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
