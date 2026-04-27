"""Failing tests for generic building panel storage lines (T106)."""

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.stone_mine import StoneMine
from game.ui.building_panel import BuildingPanel


def test_building_panel_storage_line_for_stone_mine() -> None:
    b = StoneMine(level=1, grid_pos=(10, 10))
    b.add_to_storage(1)
    assert BuildingPanel.storage_line(b) == "Storage: 1 / 3"


def test_building_panel_storage_line_for_iron_mine() -> None:
    b = IronMine(level=2, grid_pos=(10, 10))
    assert BuildingPanel.storage_line(b) == "Storage: 0 / 5"


def test_building_panel_storage_line_for_farm_updates_after_level_up() -> None:
    b = Farm(level=1, grid_pos=(10, 10))
    b.add_to_storage(1)
    assert BuildingPanel.storage_line(b) == "Storage: 1 / 3"
    b.level = 4
    assert BuildingPanel.storage_line(b) == "Storage: 1 / 9"
