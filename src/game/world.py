"""Playable isometric grid with occupancy, tree entities, and reservations."""

from __future__ import annotations

from collections import deque
import math
import random
import secrets
from typing import Any, cast

from game.config import (
    GRID_SIZE,
    WORLD_IRON_ZONE_COUNT,
    WORLD_SCATTER_TREE_FRACTION,
    WORLD_STONE_CENTER_COUNT,
    WORLD_TREE_GROVE_COUNT,
    town_hall_footprint_tiles,
)
from game.gold import GoldDeposit
from game.iron import IronDeposit
from game.stones import Stone
from game.trees import Tree, TreeStage

_GOLD_EDGE_BAND = 5
_GOLD_CORE_RADIUS_MIN = 1
_GOLD_CORE_RADIUS_MAX = 2
_GOLD_FRAGMENT_RING_MIN = 2
_GOLD_FRAGMENT_RING_MAX = 4
_GOLD_FRAGMENT_PROBABILITY = 0.52
_IRON_ZONE_COUNT = WORLD_IRON_ZONE_COUNT
_IRON_NEAR_TH_RING_CHEB = 30
_IRON_FAR_MIN_DISTANCE_FROM_TOWN_HALL = 31
_IRON_CORE_RADIUS_MIN = 1
_IRON_CORE_RADIUS_MAX = 2
_IRON_FRAGMENT_RING_MIN = 2
_IRON_FRAGMENT_RING_MAX = 4
_IRON_FRAGMENT_PROBABILITY = 0.52
_STONE_CENTER_COUNT = WORLD_STONE_CENTER_COUNT
_STONE_GUARANTEED_TH_RING_CHEB = 20  # one cluster center: min Chebyshev to TH footprint == this
_TREE_GROVE_COUNT = WORLD_TREE_GROVE_COUNT
_STONE_MIN_DISTANCE_FROM_TOWN_HALL = 12
_TREE_GROVE_RADIUS_MIN = 5
_TREE_GROVE_RADIUS_MAX = 8
_TREE_GROVE_FILL_PROBABILITY = 0.7
_TREE_GROVE_CIRCLE_DENSE_RADIUS = 10
_TREE_GROVE_CIRCLE_MAX_RADIUS = 20
_TREE_GROVE_CRESCENT_RADIUS = 20
_TREE_GROVE_ELLIPSE_MAJOR_AXIS = 20
_TREE_GROVE_ELLIPSE_MINOR_AXIS_MIN = 4
_TREE_GROVE_ELLIPSE_MINOR_AXIS_MAX = 5
_TREE_GROVE_CLUSTER_EDGE_BAND = 10
_TREE_GROVE_CLUSTER_MAX_CENTER_DISTANCE = 35
_TREE_GROVE_CLUSTER_TARGET_MIN = 110
_TREE_GROVE_CLUSTER_TARGET_MAX = 170
_PRIORITY_TREE_RING_NEAR = 12  # first bonus grove: min Chebyshev to TH footprint
_PRIORITY_TREE_RING_FAR = 20  # second bonus grove
# L∞ disks r≤R do not overlap if center separation > 2R (here R = max grove radius).
_PRIORITY_TREE_PAIR_MIN_CENTER_SEP = 2 * _TREE_GROVE_RADIUS_MAX + 1
_SCATTER_TREE_FRACTION = WORLD_SCATTER_TREE_FRACTION
_NEIGHBORS_4: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
)

_POP_MISSING = object()


def _rotate(dx: float, dy: float, angle_rad: float) -> tuple[float, float]:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return (dx * cos_a + dy * sin_a, -dx * sin_a + dy * cos_a)


def _iter_circle_noise_falloff_tiles(
    cx: int,
    cy: int,
    rng: random.Random,
) -> set[tuple[int, int]]:
    """Circle with dense inner core and noisy falloff ring."""
    out: set[tuple[int, int]] = set()
    dense = _TREE_GROVE_CIRCLE_DENSE_RADIUS
    max_r = _TREE_GROVE_CIRCLE_MAX_RADIUS
    for y in range(cy - max_r, cy + max_r + 1):
        for x in range(cx - max_r, cx + max_r + 1):
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy)
            if dist > max_r:
                continue
            if dist <= dense:
                density = 0.92
            else:
                fade = (max_r - dist) / max(1.0, max_r - dense)
                density = 0.2 + 0.55 * max(0.0, fade)
            density *= 0.8 + 0.4 * rng.random()
            if rng.random() < density:
                out.add((x, y))
    return out


def _iter_crescent_tiles(cx: int, cy: int, rng: random.Random) -> set[tuple[int, int]]:
    """Rotated crescent (outer disk minus shifted inner disk)."""
    out: set[tuple[int, int]] = set()
    outer = _TREE_GROVE_CRESCENT_RADIUS
    inner = 14.5
    shift = 8.0
    angle = rng.random() * math.tau
    for y in range(cy - outer, cy + outer + 1):
        for x in range(cx - outer, cx + outer + 1):
            dx = float(x - cx)
            dy = float(y - cy)
            u, v = _rotate(dx, dy, angle)
            in_outer = (u * u + v * v) <= (outer * outer)
            du = u - shift
            in_inner = (du * du + v * v) <= (inner * inner)
            if not in_outer or in_inner:
                continue
            edge = math.sqrt((u * u + v * v) / (outer * outer))
            density = 0.85 - 0.3 * min(1.0, edge)
            if rng.random() < density:
                out.add((x, y))
    return out


def _iter_ellipse_tiles(cx: int, cy: int, rng: random.Random) -> set[tuple[int, int]]:
    """Long rotated ellipse with thinner edges."""
    out: set[tuple[int, int]] = set()
    a = float(_TREE_GROVE_ELLIPSE_MAJOR_AXIS)
    b = float(rng.randint(_TREE_GROVE_ELLIPSE_MINOR_AXIS_MIN, _TREE_GROVE_ELLIPSE_MINOR_AXIS_MAX))
    angle = rng.random() * math.tau
    reach = int(math.ceil(a))
    for y in range(cy - reach, cy + reach + 1):
        for x in range(cx - reach, cx + reach + 1):
            dx = float(x - cx)
            dy = float(y - cy)
            u, v = _rotate(dx, dy, angle)
            norm = (u * u) / (a * a) + (v * v) / (b * b)
            if norm > 1.0:
                continue
            density = 0.9 - 0.45 * norm
            if rng.random() < density:
                out.add((x, y))
    return out


def _iter_cluster_tiles(cx: int, cy: int, rng: random.Random) -> set[tuple[int, int]]:
    """Organic cluster grown by randomized queue expansion."""
    out: set[tuple[int, int]] = set()
    edge_candidates: list[tuple[int, int]] = []
    for gy in range(GRID_SIZE):
        for gx in range(GRID_SIZE):
            edge_dist = min(gx, gy, GRID_SIZE - 1 - gx, GRID_SIZE - 1 - gy)
            if edge_dist > _TREE_GROVE_CLUSTER_EDGE_BAND:
                continue
            if max(abs(gx - cx), abs(gy - cy)) > _TREE_GROVE_CLUSTER_MAX_CENTER_DISTANCE:
                continue
            edge_candidates.append((gx, gy))
    if not edge_candidates:
        seed = (cx, cy)
    else:
        seed = edge_candidates[rng.randrange(len(edge_candidates))]
    q: deque[tuple[int, int]] = deque([seed])
    seen: set[tuple[int, int]] = {seed}
    target = rng.randint(_TREE_GROVE_CLUSTER_TARGET_MIN, _TREE_GROVE_CLUSTER_TARGET_MAX)
    while q and len(out) < target:
        px, py = q.popleft()
        out.add((px, py))
        neighbors = [(px + dx, py + dy) for dx, dy in _NEIGHBORS_4]
        rng.shuffle(neighbors)
        for nx, ny in neighbors:
            tile = (nx, ny)
            if tile in seen:
                continue
            seen.add(tile)
            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
                continue
            if max(abs(nx - cx), abs(ny - cy)) > _TREE_GROVE_CLUSTER_MAX_CENTER_DISTANCE:
                continue
            if rng.random() < 0.72:
                q.append(tile)
        if q and rng.random() < 0.08:
            q.rotate(rng.randint(-3, 3))
    return out


def _iter_stone_circle_noise_tiles(cx: int, cy: int, radius: int, rng: random.Random) -> set[tuple[int, int]]:
    """Circle-like blob with noisy boundary."""
    out: set[tuple[int, int]] = set()
    dense_r = max(1.0, radius * 0.6)
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy)
            if dist > radius:
                continue
            if dist <= dense_r:
                density = 0.92
            else:
                fade = (radius - dist) / max(1.0, radius - dense_r)
                density = 0.25 + 0.6 * max(0.0, fade)
            density *= 0.8 + 0.4 * rng.random()
            if rng.random() < density:
                out.add((x, y))
    return out


def _iter_stone_frontier_tiles(cx: int, cy: int, radius: int, rng: random.Random) -> set[tuple[int, int]]:
    """Grow a lumpy connected patch from center via randomized frontier expansion."""
    target = rng.randint(max(6, radius * radius // 2), max(10, radius * radius + 6))
    out: set[tuple[int, int]] = set()
    frontier: deque[tuple[int, int]] = deque([(cx, cy)])
    seen: set[tuple[int, int]] = {(cx, cy)}
    while frontier and len(out) < target:
        px, py = frontier.popleft()
        if max(abs(px - cx), abs(py - cy)) > radius:
            continue
        out.add((px, py))
        nbrs = [(px + dx, py + dy) for dx, dy in _NEIGHBORS_4]
        rng.shuffle(nbrs)
        for nx, ny in nbrs:
            tile = (nx, ny)
            if tile in seen:
                continue
            seen.add(tile)
            if max(abs(nx - cx), abs(ny - cy)) > radius:
                continue
            if rng.random() < 0.72:
                frontier.append(tile)
        if frontier and rng.random() < 0.15:
            frontier.rotate(rng.randint(-2, 2))
    return out


def _iter_stone_morph_blob_tiles(cx: int, cy: int, radius: int, rng: random.Random) -> set[tuple[int, int]]:
    """Blob with one pass of random erosion/dilation to produce broken edges."""
    base: set[tuple[int, int]] = set()
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if max(abs(x - cx), abs(y - cy)) > radius:
                continue
            if rng.random() < 0.72:
                base.add((x, y))

    # Erode sparse-edge pixels.
    eroded: set[tuple[int, int]] = set()
    for x, y in base:
        neigh = 0
        for dx, dy in _NEIGHBORS_4:
            if (x + dx, y + dy) in base:
                neigh += 1
        if neigh >= 2 or rng.random() < 0.2:
            eroded.add((x, y))

    # Dilate back selected boundary to avoid over-thinning.
    out = set(eroded)
    for x, y in list(eroded):
        if rng.random() < 0.25:
            for dx, dy in _NEIGHBORS_4:
                nx, ny = x + dx, y + dy
                if max(abs(nx - cx), abs(ny - cy)) <= radius:
                    out.add((nx, ny))
    return out


def _iter_stone_cluster_pattern_tiles(
    cx: int, cy: int, radius: int, rng: random.Random
) -> set[tuple[int, int]]:
    pattern = rng.choice(("circle_noise", "frontier", "morph_blob"))
    if pattern == "circle_noise":
        return _iter_stone_circle_noise_tiles(cx, cy, radius, rng)
    if pattern == "frontier":
        return _iter_stone_frontier_tiles(cx, cy, radius, rng)
    return _iter_stone_morph_blob_tiles(cx, cy, radius, rng)


def _iter_tree_grove_pattern_tiles(
    cx: int,
    cy: int,
    rng: random.Random,
) -> set[tuple[int, int]]:
    """Pick one grove pattern randomly for each center."""
    pattern = rng.choice(("circle_noise", "crescent", "ellipse", "cluster"))
    if pattern == "circle_noise":
        return _iter_circle_noise_falloff_tiles(cx, cy, rng)
    if pattern == "crescent":
        return _iter_crescent_tiles(cx, cy, rng)
    if pattern == "ellipse":
        return _iter_ellipse_tiles(cx, cy, rng)
    return _iter_cluster_tiles(cx, cy, rng)


def _iter_compact_priority_grove_tiles(
    cx: int,
    cy: int,
    rng: random.Random,
) -> set[tuple[int, int]]:
    """Small, dense grove footprint used for TH-near priority centers."""
    out: set[tuple[int, int]] = set()
    radius = rng.randint(_TREE_GROVE_RADIUS_MIN, _TREE_GROVE_RADIUS_MAX)
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            dx = x - cx
            dy = y - cy
            if math.hypot(dx, dy) > radius:
                continue
            # Keep compact center dense, fade edges a bit.
            edge = math.hypot(dx, dy) / max(1.0, float(radius))
            density = 0.9 - 0.35 * edge
            if rng.random() < density:
                out.add((x, y))
    return out


def _world_generation_rngs(
    world_seed: int | None,
) -> tuple[random.Random, random.Random, random.Random, random.Random]:
    """RNGs for gold, iron, stones, and trees. ``world_seed`` set ⇒ reproducible."""
    if world_seed is not None:
        s = (world_seed % (2**31 - 2)) + 1
        return (
            random.Random(s * 1_579_241 + 29),
            random.Random(s * 1_311_223 + 71),
            random.Random(s * 1_047_269 + 17),
            random.Random(s * 912_367 + 43),
        )
    buf = secrets.token_bytes(32)
    return (
        random.Random(int.from_bytes(buf[:8], "big")),
        random.Random(int.from_bytes(buf[8:16], "big")),
        random.Random(int.from_bytes(buf[16:24], "big")),
        random.Random(int.from_bytes(buf[24:], "big")),
    )


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
        o._blocked_tiles = set(o._occupied_tiles) | o._stone_tiles | o._iron_blocking_tiles | o._gold_blocking_tiles


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
        o._blocked_tiles = set(o._occupied_tiles) | o._tree_tiles | o._iron_blocking_tiles | o._gold_blocking_tiles


class _IronLayerDict(dict[tuple[int, int], IronDeposit]):
    """`_iron` storage that keeps iron tile caches in sync on mutation."""

    __slots__ = ("_owner",)

    def __init__(self, owner: World) -> None:
        super().__init__()
        self._owner = owner

    def __setitem__(self, key: tuple[int, int], value: IronDeposit) -> None:
        old = self.get(key)
        if old is not None and old.blocking:
            self._owner._iron_blocking_tiles.discard(key)
            self._owner._blocked_tiles.discard(key)
        super().__setitem__(key, value)
        self._owner._iron_tiles.add(key)
        if value.blocking:
            self._owner._iron_blocking_tiles.add(key)
            self._owner._blocked_tiles.add(key)

    def __delitem__(self, key: tuple[int, int]) -> None:
        old = self.get(key)
        super().__delitem__(key)
        self._owner._iron_tiles.discard(key)
        if old is not None and old.blocking:
            self._owner._iron_blocking_tiles.discard(key)
            self._owner._blocked_tiles.discard(key)

    def pop(self, key: tuple[int, int], default: Any = _POP_MISSING) -> IronDeposit:
        if key not in self:
            if default is _POP_MISSING:
                raise KeyError(key)
            return cast("IronDeposit", default)
        value = super().__getitem__(key)
        del self[key]
        return value

    def clear(self) -> None:
        super().clear()
        o = self._owner
        o._iron_tiles.clear()
        o._iron_blocking_tiles.clear()
        o._blocked_tiles = set(o._occupied_tiles) | o._tree_tiles | o._stone_tiles | o._gold_blocking_tiles


class _GoldLayerDict(dict[tuple[int, int], GoldDeposit]):
    """`_gold` storage that keeps gold tile caches in sync on mutation."""

    __slots__ = ("_owner",)

    def __init__(self, owner: World) -> None:
        super().__init__()
        self._owner = owner

    def __setitem__(self, key: tuple[int, int], value: GoldDeposit) -> None:
        old = self.get(key)
        if old is not None and old.blocking:
            self._owner._gold_blocking_tiles.discard(key)
            self._owner._blocked_tiles.discard(key)
        super().__setitem__(key, value)
        self._owner._gold_tiles.add(key)
        if value.blocking:
            self._owner._gold_blocking_tiles.add(key)
            self._owner._blocked_tiles.add(key)

    def __delitem__(self, key: tuple[int, int]) -> None:
        old = self.get(key)
        super().__delitem__(key)
        self._owner._gold_tiles.discard(key)
        if old is not None and old.blocking:
            self._owner._gold_blocking_tiles.discard(key)
            self._owner._blocked_tiles.discard(key)

    def pop(self, key: tuple[int, int], default: Any = _POP_MISSING) -> GoldDeposit:
        if key not in self:
            if default is _POP_MISSING:
                raise KeyError(key)
            return cast("GoldDeposit", default)
        value = super().__getitem__(key)
        del self[key]
        return value

    def clear(self) -> None:
        super().clear()
        o = self._owner
        o._gold_tiles.clear()
        o._gold_blocking_tiles.clear()
        o._blocked_tiles = set(o._occupied_tiles) | o._tree_tiles | o._stone_tiles | o._iron_blocking_tiles


class World:
    """Square `GRID_SIZE`×`GRID_SIZE` grass field with occupancy and trees."""

    __slots__ = (
        "_occupied",
        "_occupied_tiles",
        "_trees",
        "_tree_tiles",
        "_stones",
        "_stone_tiles",
        "_gold",
        "_gold_tiles",
        "_gold_blocking_tiles",
        "_iron",
        "_iron_tiles",
        "_iron_blocking_tiles",
        "_blocked_tiles",
        "_tree_reservations",
        "_stone_reservations",
        "_stone_centers",
        "_gold_center",
        "_iron_centers",
        "_tree_centers",
        "_scatter_trees_placed",
    )

    def __init__(self, *, world_seed: int | None = None) -> None:
        self._occupied: list[list[bool]] = [
            [False] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        self._occupied_tiles: set[tuple[int, int]] = set()
        self._trees = _TreeLayerDict(self)
        self._tree_tiles: set[tuple[int, int]] = set()
        self._stones = _StoneLayerDict(self)
        self._stone_tiles: set[tuple[int, int]] = set()
        self._gold = _GoldLayerDict(self)
        self._gold_tiles: set[tuple[int, int]] = set()
        self._gold_blocking_tiles: set[tuple[int, int]] = set()
        self._iron = _IronLayerDict(self)
        self._iron_tiles: set[tuple[int, int]] = set()
        self._iron_blocking_tiles: set[tuple[int, int]] = set()
        self._blocked_tiles: set[tuple[int, int]] = set()
        self._tree_reservations: dict[tuple[int, int], object] = {}
        self._stone_reservations: dict[tuple[int, int], object] = {}
        self._stone_centers: list[tuple[int, int]] = []
        self._gold_center: tuple[int, int] | None = None
        self._iron_centers: list[tuple[int, int]] = []
        self._tree_centers: list[tuple[int, int]] = []
        self._scatter_trees_placed = 0
        gold_rng, iron_rng, stone_rng, tree_rng = _world_generation_rngs(world_seed)
        self._init_gold(gold_rng)
        self._init_iron(iron_rng)
        self._init_stones(stone_rng)
        self._init_trees(tree_rng)

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

    def iron_tiles(self) -> set[tuple[int, int]]:
        """All iron tiles, both blocking rifts and buildable ore fragments."""
        return set(self._iron_tiles)

    def gold_tiles(self) -> set[tuple[int, int]]:
        """All gold tiles, both blocking veins and buildable ore fragments."""
        return set(self._gold_tiles)

    def gold_blocking_tiles(self) -> set[tuple[int, int]]:
        """Blocking central gold vein tiles."""
        return set(self._gold_blocking_tiles)

    def gold_buildable_tiles(self) -> set[tuple[int, int]]:
        """Passable gold fragment tiles reserved for future gold mine placement."""
        return self._gold_tiles - self._gold_blocking_tiles

    def iron_blocking_tiles(self) -> set[tuple[int, int]]:
        """Blocking central iron rift tiles."""
        return set(self._iron_blocking_tiles)

    def iron_buildable_tiles(self) -> set[tuple[int, int]]:
        """Passable iron fragment tiles where iron mines may be placed."""
        return self._iron_tiles - self._iron_blocking_tiles

    def blocked_tiles(self) -> set[tuple[int, int]]:
        """Union of building footprints, alive trees, stones, and blocking metal deposits."""
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
        self._gold_tiles = set(self._gold.keys())
        self._gold_blocking_tiles = {tile for tile, gold in self._gold.items() if gold.blocking}
        self._iron_tiles = set(self._iron.keys())
        self._iron_blocking_tiles = {tile for tile, iron in self._iron.items() if iron.blocking}
        self._blocked_tiles = (
            set(self._occupied_tiles)
            | self._tree_tiles
            | self._stone_tiles
            | self._iron_blocking_tiles
            | self._gold_blocking_tiles
        )

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

    def plant_tree(self, gx: int, gy: int, *, now_ms: int, species: int | None = None) -> Tree | None:
        """Plant a new sapling on a valid free tile, else return ``None``."""
        tile = (gx, gy)
        if not self.is_in_grass(gx, gy):
            return None
        if tile in town_hall_footprint_tiles():
            return None
        if self.is_occupied(gx, gy):
            return None
        if self.is_stone_blocking(gx, gy):
            return None
        if self.iron_deposit_at(gx, gy) is not None:
            return None
        if self.gold_deposit_at(gx, gy) is not None:
            return None
        if self.tree_at(gx, gy) is not None:
            return None
        chosen_species = random.randint(0, 2) if species is None else int(species)
        planted = Tree(stage=TreeStage.SAPLING, species=chosen_species, next_growth_at_ms=int(now_ms) + 30_000)
        self._trees[tile] = planted
        return planted

    def update(self, now_ms: int) -> None:
        """Advance world state for this frame (e.g. tree growth)."""
        self.update_tree_growth(now_ms=now_ms)

    def update_tree_growth(self, *, now_ms: int) -> None:
        """Advance all alive trees with growth timers based on ``now_ms``."""
        for tree in self._trees.values():
            if tree.alive:
                tree.update_growth(int(now_ms))

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

    def iron_deposit_at(self, gx: int, gy: int) -> IronDeposit | None:
        if not self.is_in_grass(gx, gy):
            return None
        return self._iron.get((gx, gy))

    def gold_deposit_at(self, gx: int, gy: int) -> GoldDeposit | None:
        if not self.is_in_grass(gx, gy):
            return None
        return self._gold.get((gx, gy))

    def is_gold_blocking(self, gx: int, gy: int) -> bool:
        gold = self.gold_deposit_at(gx, gy)
        return gold is not None and gold.blocking

    def is_gold_buildable(self, gx: int, gy: int) -> bool:
        gold = self.gold_deposit_at(gx, gy)
        return gold is not None and gold.buildable

    def iter_gold_deposits(self) -> list[tuple[tuple[int, int], GoldDeposit]]:
        return list(self._gold.items())

    def is_iron_blocking(self, gx: int, gy: int) -> bool:
        iron = self.iron_deposit_at(gx, gy)
        return iron is not None and iron.blocking

    def is_iron_buildable(self, gx: int, gy: int) -> bool:
        iron = self.iron_deposit_at(gx, gy)
        return iron is not None and iron.buildable

    def iter_iron_deposits(self) -> list[tuple[tuple[int, int], IronDeposit]]:
        return list(self._iron.items())

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
                    if (
                        tile not in self._tree_tiles
                        and tile not in self._stone_tiles
                        and tile not in self._iron_blocking_tiles
                        and tile not in self._gold_blocking_tiles
                    ):
                        self._blocked_tiles.discard(tile)

    def _plant_tree_grove(
        self,
        cx: int,
        cy: int,
        rng: random.Random,
        *,
        mid: int,
        center_clear_radius: int,
        protected_th: set[tuple[int, int]],
        relax_map_center_clear: bool,
    ) -> None:
        # Guarantee a visible anchor tree on priority grove centers (ring 12 / ring 20).
        if relax_map_center_clear:
            if (
                self.is_in_grass(cx, cy)
                and (cx, cy) not in protected_th
                and not self.is_stone_blocking(cx, cy)
                and self.iron_deposit_at(cx, cy) is None
                and self.gold_deposit_at(cx, cy) is None
                and (cx, cy) not in self._trees
            ):
                self._trees[(cx, cy)] = Tree(stage=TreeStage.ADULT, species=rng.randint(0, 2))

        candidate_tiles = (
            _iter_compact_priority_grove_tiles(cx, cy, rng)
            if relax_map_center_clear
            else _iter_tree_grove_pattern_tiles(cx, cy, rng)
        )
        for x, y in candidate_tiles:
            if not self.is_in_grass(x, y):
                continue
            if (x, y) in protected_th:
                continue
            if self.is_stone_blocking(x, y):
                continue
            if self.iron_deposit_at(x, y) is not None:
                continue
            if self.gold_deposit_at(x, y) is not None:
                continue
            if (x, y) in self._trees:
                continue
            if rng.random() >= _TREE_GROVE_FILL_PROBABILITY:
                continue
            self._trees[(x, y)] = Tree(stage=TreeStage.ADULT, species=rng.randint(0, 2))

    def _init_trees(self, rng: random.Random) -> None:
        mid = GRID_SIZE // 2
        center_clear_radius = max(8, GRID_SIZE // 4)
        protected_th = town_hall_footprint_tiles()
        priority = _pick_pair_priority_tree_grove_centers(self, rng)
        exclude = set(priority)
        far = _pick_far_cluster_centers(
            self, _TREE_GROVE_COUNT, rng, forbid_stone_center=True, exclude=exclude
        )
        self._tree_centers = priority + far
        priority_set = set(priority)
        for cx, cy in self._tree_centers:
            self._plant_tree_grove(
                cx,
                cy,
                rng,
                mid=mid,
                center_clear_radius=center_clear_radius,
                protected_th=protected_th,
                relax_map_center_clear=(cx, cy) in priority_set,
            )

        self._scatter_random_trees(rng, mid, center_clear_radius)

    def _scatter_random_trees(
        self, rng: random.Random, mid: int, center_clear_radius: int
    ) -> None:
        """Place extra trees on random grass (same passability rules as groves, no overlap)."""
        area = GRID_SIZE * GRID_SIZE
        target = int(area * _SCATTER_TREE_FRACTION)
        if target <= 0:
            self._scatter_trees_placed = 0
            return
        eligible: list[tuple[int, int]] = []
        for gy in range(GRID_SIZE):
            for gx in range(GRID_SIZE):
                if not self.is_in_grass(gx, gy):
                    continue
                if max(abs(gx - mid), abs(gy - mid)) <= center_clear_radius:
                    continue
                if self.is_stone_blocking(gx, gy):
                    continue
                if self.iron_deposit_at(gx, gy) is not None:
                    continue
                if self.gold_deposit_at(gx, gy) is not None:
                    continue
                if (gx, gy) in self._trees:
                    continue
                eligible.append((gx, gy))
        rng.shuffle(eligible)
        placed = 0
        for gx, gy in eligible:
            if placed >= target:
                break
            self._trees[(gx, gy)] = Tree(stage=TreeStage.ADULT, species=rng.randint(0, 2))
            placed += 1
        self._scatter_trees_placed = placed

    def _init_gold(self, rng: random.Random) -> None:
        self._gold_center = _pick_gold_zone_center(self, rng)
        if self._gold_center is None:
            return
        cx, cy = self._gold_center
        protected_th = town_hall_footprint_tiles()
        core_radius = rng.randint(_GOLD_CORE_RADIUS_MIN, _GOLD_CORE_RADIUS_MAX)
        core_tiles = _iter_stone_cluster_pattern_tiles(cx, cy, core_radius, rng)
        placed_core_tiles: set[tuple[int, int]] = set()
        for x, y in core_tiles:
            if not self.is_in_grass(x, y):
                continue
            if (x, y) in protected_th:
                continue
            self._gold[(x, y)] = GoldDeposit(blocking=True, variant=rng.randint(0, 4))
            placed_core_tiles.add((x, y))

        if not placed_core_tiles:
            return
        fragment_depth = rng.randint(_GOLD_FRAGMENT_RING_MIN, _GOLD_FRAGMENT_RING_MAX)
        min_x = min(x for x, _y in placed_core_tiles) - fragment_depth
        max_x = max(x for x, _y in placed_core_tiles) + fragment_depth
        min_y = min(y for _x, y in placed_core_tiles) - fragment_depth
        max_y = max(y for _x, y in placed_core_tiles) + fragment_depth
        for layer in range(1, fragment_depth + 1):
            layer_candidates: list[tuple[int, int]] = []
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    if not self.is_in_grass(x, y):
                        continue
                    if (x, y) in protected_th or (x, y) in self._gold:
                        continue
                    dist_to_core = min(max(abs(x - gx), abs(y - gy)) for gx, gy in placed_core_tiles)
                    if dist_to_core != layer:
                        continue
                    if layer > 1 and not any(
                        self.gold_deposit_at(x + dx, y + dy) is not None
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                        if dx != 0 or dy != 0
                    ):
                        continue
                    layer_candidates.append((x, y))
            rng.shuffle(layer_candidates)
            for x, y in layer_candidates:
                if layer == 1:
                    probability = 1.0
                else:
                    probability = _GOLD_FRAGMENT_PROBABILITY * (1.15 - 0.18 * (layer - 1))
                if rng.random() < probability:
                    self._gold[(x, y)] = GoldDeposit(blocking=False, variant=rng.randint(0, 4))

    def _init_iron(self, rng: random.Random) -> None:
        self._iron_centers = _pick_iron_zone_centers(self, rng)
        protected_th = town_hall_footprint_tiles()
        for cx, cy in self._iron_centers:
            core_radius = rng.randint(_IRON_CORE_RADIUS_MIN, _IRON_CORE_RADIUS_MAX)
            core_tiles = _iter_stone_cluster_pattern_tiles(cx, cy, core_radius, rng)
            placed_core_tiles: set[tuple[int, int]] = set()
            for x, y in core_tiles:
                if not self.is_in_grass(x, y):
                    continue
                if (x, y) in protected_th:
                    continue
                if self.gold_deposit_at(x, y) is not None:
                    continue
                self._iron[(x, y)] = IronDeposit(blocking=True, variant=rng.randint(0, 4))
                placed_core_tiles.add((x, y))

            if not placed_core_tiles:
                continue
            fragment_depth = rng.randint(_IRON_FRAGMENT_RING_MIN, _IRON_FRAGMENT_RING_MAX)
            min_x = min(x for x, _y in placed_core_tiles) - fragment_depth
            max_x = max(x for x, _y in placed_core_tiles) + fragment_depth
            min_y = min(y for _x, y in placed_core_tiles) - fragment_depth
            max_y = max(y for _x, y in placed_core_tiles) + fragment_depth
            for layer in range(1, fragment_depth + 1):
                layer_candidates: list[tuple[int, int]] = []
                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        if not self.is_in_grass(x, y):
                            continue
                        if (x, y) in protected_th or (x, y) in self._iron:
                            continue
                        if self.gold_deposit_at(x, y) is not None:
                            continue
                        dist_to_core = min(max(abs(x - ix), abs(y - iy)) for ix, iy in placed_core_tiles)
                        if dist_to_core != layer:
                            continue
                        if layer > 1 and not any(
                            self.iron_deposit_at(x + dx, y + dy) is not None
                            for dx in (-1, 0, 1)
                            for dy in (-1, 0, 1)
                            if dx != 0 or dy != 0
                        ):
                            continue
                        layer_candidates.append((x, y))
                rng.shuffle(layer_candidates)
                for x, y in layer_candidates:
                    if layer == 1:
                        probability = 1.0
                    else:
                        probability = _IRON_FRAGMENT_PROBABILITY * (1.15 - 0.18 * (layer - 1))
                    if rng.random() < probability:
                        self._iron[(x, y)] = IronDeposit(blocking=False, variant=rng.randint(0, 4))

    def _init_stones(self, rng: random.Random) -> None:
        self._stone_centers, ring_center = _pick_stone_cluster_centers(self, rng)
        mid = GRID_SIZE // 2
        center_clear_radius = max(8, GRID_SIZE // 4)
        protected_th = town_hall_footprint_tiles()

        for cx, cy in self._stone_centers:
            radius = rng.randint(1, 4)
            relax_center_clear = ring_center is not None and (cx, cy) == ring_center
            for x, y in _iter_stone_cluster_pattern_tiles(cx, cy, radius, rng):
                if not self.is_in_grass(x, y):
                    continue
                if (x, y) in protected_th:
                    continue
                if not relax_center_clear and max(abs(x - mid), abs(y - mid)) <= center_clear_radius:
                    continue
                if self.is_tree_blocking(x, y):
                    continue
                if self.iron_deposit_at(x, y) is not None:
                    continue
                if self.gold_deposit_at(x, y) is not None:
                    continue
                if (x, y) in self._stones:
                    continue
                tile = (x, y)
                self._stones[tile] = Stone(variant=rng.randint(0, 4))


def _min_chebyshev_to_tiles(px: int, py: int, tiles: set[tuple[int, int]]) -> int:
    return min(max(abs(px - tx), abs(py - ty)) for tx, ty in tiles)


def _chebyshev_point_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _cheb_disk_has_no_stones(world: World, cx: int, cy: int, r: int) -> bool:
    """True iff every in-bounds tile in the Chebyshev disk (Chebyshev ≤ r) has no stone."""
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if not world.is_in_grass(x, y):
                continue
            if max(abs(x - cx), abs(y - cy)) > r:
                continue
            if world.is_stone_blocking(x, y):
                return False
    return True


def _ring_center_candidates_no_stone_disk(
    world: World, ring: int, disk_r: int
) -> list[tuple[int, int]]:
    protected = town_hall_footprint_tiles()
    out: list[tuple[int, int]] = []
    for cy in range(GRID_SIZE):
        for cx in range(GRID_SIZE):
            if not world.is_in_grass(cx, cy):
                continue
            if _min_chebyshev_to_tiles(cx, cy, protected) != ring:
                continue
            if world.is_stone_blocking(cx, cy):
                continue
            if not _cheb_disk_has_no_stones(world, cx, cy, disk_r):
                continue
            out.append((cx, cy))
    return out


def _ring_center_candidates(world: World, ring: int) -> list[tuple[int, int]]:
    """Candidates exactly on a TH-distance ring, requiring only in-bounds + no stone at center."""
    protected = town_hall_footprint_tiles()
    out: list[tuple[int, int]] = []
    for cy in range(GRID_SIZE):
        for cx in range(GRID_SIZE):
            if not world.is_in_grass(cx, cy):
                continue
            if _min_chebyshev_to_tiles(cx, cy, protected) != ring:
                continue
            if world.is_stone_blocking(cx, cy):
                continue
            out.append((cx, cy))
    return out


def _pick_pair_priority_tree_grove_centers(world: World, rng: random.Random) -> list[tuple[int, int]]:
    """Up to two centers: ring ``_PRIORITY_TREE_RING_NEAR`` then ``_PRIORITY_TREE_RING_FAR`` from TH.

    The Chebyshev disks of radius ``_TREE_GROVE_RADIUS_MAX`` around each center must contain
    no stone tiles; the two centers must be at least ``_PRIORITY_TREE_PAIR_MIN_CENTER_SEP``
    apart (Chebyshev) so max-radius groves cannot overlap. Returns ``[]`` if no valid pair.
    """
    r_ball = _TREE_GROVE_RADIUS_MAX
    ring_near = _ring_center_candidates_no_stone_disk(world, _PRIORITY_TREE_RING_NEAR, r_ball)
    ring_far = _ring_center_candidates_no_stone_disk(world, _PRIORITY_TREE_RING_FAR, r_ball)
    rng.shuffle(ring_near)
    rng.shuffle(ring_far)
    min_sep = _PRIORITY_TREE_PAIR_MIN_CENTER_SEP
    for a in ring_near:
        for b in ring_far:
            if _chebyshev_point_distance(a, b) >= min_sep:
                return [a, b]
    # Fallback 1: keep both rings even if separation rule cannot be satisfied.
    if ring_near and ring_far:
        return [ring_near[0], ring_far[0]]

    # Fallback 2: relax "no stones in full grove disk", keep exact ring requirement.
    relaxed_near = _ring_center_candidates(world, _PRIORITY_TREE_RING_NEAR)
    relaxed_far = _ring_center_candidates(world, _PRIORITY_TREE_RING_FAR)
    rng.shuffle(relaxed_near)
    rng.shuffle(relaxed_far)
    if relaxed_near and relaxed_far:
        for a in relaxed_near:
            for b in relaxed_far:
                if _chebyshev_point_distance(a, b) >= min_sep:
                    return [a, b]
        return [relaxed_near[0], relaxed_far[0]]
    return []


def _pick_stone_cluster_centers(
    world: World, rng: random.Random
) -> tuple[list[tuple[int, int]], tuple[int, int] | None]:
    """Pick ``_STONE_CENTER_COUNT`` centers; one on TH Chebyshev ring 20 if any candidate exists.

    Returns ``(centers, ring_center)`` where ``ring_center`` is the mandatory ring tile (for
    relaxed map-center clearing when filling stones) or ``None``.
    """
    protected = town_hall_footprint_tiles()
    ring_candidates: list[tuple[int, int]] = []
    for cy in range(GRID_SIZE):
        for cx in range(GRID_SIZE):
            if not world.is_in_grass(cx, cy):
                continue
            if _min_chebyshev_to_tiles(cx, cy, protected) != _STONE_GUARANTEED_TH_RING_CHEB:
                continue
            ring_candidates.append((cx, cy))
    rng.shuffle(ring_candidates)
    centers: list[tuple[int, int]] = []
    exclude: set[tuple[int, int]] = set()
    ring_center: tuple[int, int] | None = None
    if ring_candidates:
        ring_center = ring_candidates[0]
        centers.append(ring_center)
        exclude.add(ring_center)
    need = _STONE_CENTER_COUNT - len(centers)
    centers.extend(
        _pick_far_cluster_centers(world, need, rng, forbid_stone_center=False, exclude=exclude)
    )
    exclude = set(centers)
    while len(centers) < _STONE_CENTER_COUNT:
        more = _pick_far_cluster_centers(
            world,
            _STONE_CENTER_COUNT - len(centers),
            rng,
            forbid_stone_center=False,
            exclude=exclude,
        )
        if not more:
            break
        centers.extend(more)
        exclude.update(more)
    return centers, ring_center


def _pick_gold_zone_center(world: World, rng: random.Random) -> tuple[int, int] | None:
    protected = town_hall_footprint_tiles()
    min_from_edge = 2
    max_from_edge = min(GRID_SIZE - 1, _GOLD_EDGE_BAND)
    candidates = [
        (cx, cy)
        for cy in range(GRID_SIZE)
        for cx in range(GRID_SIZE)
        if world.is_in_grass(cx, cy)
        and min(cx, cy, GRID_SIZE - 1 - cx, GRID_SIZE - 1 - cy) <= max_from_edge
        and min(cx, cy, GRID_SIZE - 1 - cx, GRID_SIZE - 1 - cy) >= min_from_edge
        and (cx, cy) not in protected
        and _min_chebyshev_to_tiles(cx, cy, protected) >= 30
    ]
    if not candidates:
        return None
    return rng.choice(candidates)


def _pick_iron_zone_centers(world: World, rng: random.Random) -> list[tuple[int, int]]:
    protected = town_hall_footprint_tiles()

    def min_th(cx: int, cy: int) -> int:
        return _min_chebyshev_to_tiles(cx, cy, protected)

    near = [
        (cx, cy)
        for cy in range(GRID_SIZE)
        for cx in range(GRID_SIZE)
        if world.is_in_grass(cx, cy) and min_th(cx, cy) == _IRON_NEAR_TH_RING_CHEB
    ]
    far = [
        (cx, cy)
        for cy in range(GRID_SIZE)
        for cx in range(GRID_SIZE)
        if world.is_in_grass(cx, cy) and min_th(cx, cy) >= _IRON_FAR_MIN_DISTANCE_FROM_TOWN_HALL
    ]
    rng.shuffle(near)
    rng.shuffle(far)
    centers: list[tuple[int, int]] = []
    if near:
        centers.append(near[0])
    min_sep = _IRON_CORE_RADIUS_MAX * 2 + _IRON_FRAGMENT_RING_MAX + 2
    for candidate in far:
        if all(_chebyshev_point_distance(candidate, existing) >= min_sep for existing in centers):
            centers.append(candidate)
            break
    if len(centers) < _IRON_ZONE_COUNT:
        for candidate in far:
            if candidate not in centers:
                centers.append(candidate)
                break
    return centers[:_IRON_ZONE_COUNT]


def _pick_far_cluster_centers(
    world: World,
    count: int,
    rng: random.Random,
    *,
    forbid_stone_center: bool,
    exclude: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    """Pick up to `count` grass tiles outside the build clearing, Chebyshev ≥ TH distance."""
    mid = GRID_SIZE // 2
    center_clear_radius = max(8, GRID_SIZE // 4)
    protected = town_hall_footprint_tiles()
    banned = exclude or set()
    candidates = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
    rng.shuffle(candidates)
    centers: list[tuple[int, int]] = []
    for cx, cy in candidates:
        if len(centers) >= count:
            break
        if (cx, cy) in banned:
            continue
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
        and start_tree.can_chop
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
            tile_tree = world.tree_at(nx, ny)
            if tile_tree is not None and tile_tree.can_chop:
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
