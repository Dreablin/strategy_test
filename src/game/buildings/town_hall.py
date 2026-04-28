"""Town Hall — upgradable (levels 1..10), no production income."""

from typing import ClassVar

from game.buildings.base import Building


class TownHall(Building):
    type_tag: ClassVar[str] = "TOWN_HALL"
    footprint: ClassVar[tuple[int, int]] = (3, 3)
    __slots__ = ("warehouse",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.warehouse: dict[str, int] = {"wood": 0, "stone": 0, "iron": 0, "wheat": 0, "boards": 0}

    @classmethod
    def max_level(cls) -> int:
        return 10

    @staticmethod
    def _normalize_resource(resource: str) -> str:
        key = str(resource).lower()
        if key == "food":
            return "wheat"
        return key

    def warehouse_amount(self, resource: str) -> int:
        key = self._normalize_resource(resource)
        return int(self.warehouse.get(key, 0))

    def add_to_warehouse(self, resource: str, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        key = self._normalize_resource(resource)
        self.warehouse[key] = self.warehouse_amount(key) + n

    def take_from_warehouse(self, resource: str, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        key = self._normalize_resource(resource)
        current = self.warehouse_amount(key)
        if n > current:
            raise ValueError("insufficient warehouse amount")
        self.warehouse[key] = current - n
