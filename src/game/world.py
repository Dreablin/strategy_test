"""Playable isometric grid with occupancy and world-owned tree entities."""

from game.config import GRID_SIZE
from game.trees import Tree, stage_from_tile_seed

_TREE_EDGE_BAND = 8


class World:
    """Square `GRID_SIZE`×`GRID_SIZE` grass field with occupancy and trees."""

    __slots__ = ("_occupied", "_trees")

    def __init__(self) -> None:
        self._occupied: list[list[bool]] = [
            [False] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        self._trees: dict[tuple[int, int], Tree] = {}
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
