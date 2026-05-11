"""Town Hall — upgradable (levels 1..10), no production income."""

from typing import ClassVar

from game.buildings.base import Building
from game.resource_catalog import is_town_hall_warehouse_resource


class TownHall(Building):
    type_tag: ClassVar[str] = "TOWN_HALL"
    footprint: ClassVar[tuple[int, int]] = (3, 3)
    __slots__ = ("warehouse",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.warehouse: dict[str, int] = {
            "wood": 0,
            "stone": 0,
            "iron": 0,
            "wheat": 0,
            "boards": 0,
            "flour": 0,
            "bread": 0,
            "chicken": 0,
            "beef": 0,
            "hide": 0,
            "grapes": 0,
        }

    @classmethod
    def max_level(cls) -> int:
        return 10

    @staticmethod
    def _normalize_resource(resource: str) -> str:
        return str(resource).lower()

    def warehouse_amount(self, resource: str) -> int:
        key = self._normalize_resource(resource)
        if not is_town_hall_warehouse_resource(key):
            return 0
        return int(self.warehouse.get(key, 0))

    def add_to_warehouse(self, resource: str, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        key = self._normalize_resource(resource)
        if not is_town_hall_warehouse_resource(key):
            raise ValueError("not a Town Hall warehouse resource")
        self.warehouse[key] = self.warehouse_amount(key) + n

    def take_from_warehouse(self, resource: str, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        key = self._normalize_resource(resource)
        if not is_town_hall_warehouse_resource(key):
            raise ValueError("not a Town Hall warehouse resource")
        current = self.warehouse_amount(key)
        if n > current:
            raise ValueError("insufficient warehouse amount")
        self.warehouse[key] = current - n


def bootstrap_starting_warehouse(town_hall: TownHall, amounts: dict[str, int]) -> None:
    """Apply configured starting stock to a Town Hall (e.g. new game in ``main`` only)."""
    for key, n in amounts.items():
        nn = int(n)
        if nn > 0:
            town_hall.add_to_warehouse(key, nn)
