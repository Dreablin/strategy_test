"""Playable isometric grid with occupancy and world-owned tree entities."""

from game.config import GRID_SIZE
from game.trees import Tree, stage_from_tile_seed


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
        for gy in range(GRID_SIZE):
            for gx in range(GRID_SIZE):
                if abs(gx - cx) <= 3 and abs(gy - cy) <= 3:
                    continue
                edge_dist = min(gx, gy, GRID_SIZE - 1 - gx, GRID_SIZE - 1 - gy)
                if edge_dist > 4:
                    continue
                seed = gx * 92821 + gy * 68917 + GRID_SIZE * 37
                # Denser near edge, still deterministic and varied.
                threshold = 92 - (edge_dist * 12)
                if (seed % 100) < threshold:
                    self._trees[(gx, gy)] = Tree(stage=stage_from_tile_seed(seed))
