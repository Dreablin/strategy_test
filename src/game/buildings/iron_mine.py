"""Iron Mine — produces iron when staffed."""

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin
from game.config import building_int_setting, building_setting


class IronMine(StorageMixin, Building):
    type_tag: ClassVar[str] = "IRON_MINE"
    __slots__ = ("stored", "mining_started_ms", "mining_duration_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.stored = 0
        self.mining_started_ms = 0
        self.mining_duration_ms = self.cycle_ms()

    def recipe_output(self) -> dict[str, int]:
        raw = building_setting(self.type_tag, "recipe", "output")
        return {str(k): int(v) for k, v in raw.items()}

    def output_count(self) -> int:
        return sum(self.recipe_output().values())

    def cycle_ms(self) -> int:
        return building_int_setting(self.type_tag, "production", "cycle_ms")

    def rest_ms(self) -> int:
        return building_int_setting(self.type_tag, "production", "rest_ms")

    def mining_progress(self, now_ms: int) -> float:
        if self.mining_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.mining_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.mining_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))
