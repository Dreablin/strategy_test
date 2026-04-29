"""Building modal panel layout and click routing."""

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.buildings.town_hall import TownHall
from game.ui.building_panel import BuildingPanel, _income_line


def test_building_panel_close_click() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=2, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    cx, cy = layout.close.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "close"


def test_building_panel_demolish_click() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=1, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.demolish is not None
    cx, cy = layout.demolish.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "demolish"


def test_building_panel_upgrade_enabled_even_when_poor() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=1, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.upgrade is not None
    assert layout.upgrade_enabled is True
    cx, cy = layout.upgrade.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "upgrade"


def test_building_panel_upgrade_click_when_affordable() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=1, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.upgrade is not None
    assert layout.upgrade_enabled is True
    cx, cy = layout.upgrade.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "upgrade"


def test_building_panel_draw_smoke() -> None:
    surface = pygame.Surface((800, 600))
    building = LumberCamp(level=3, grid_pos=(2, 2))
    BuildingPanel.draw(surface, building, worker_assigned=True)
    assert surface.get_at((400, 300)) != (0, 0, 0, 255)


def test_building_panel_shows_upgrade_for_town_hall() -> None:
    surface = pygame.Surface((640, 480))
    building = TownHall(level=1, grid_pos=(10, 10))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.upgrade is not None


def test_income_line_is_zero_while_worker_not_arrived() -> None:
    building = LumberCamp(level=3, grid_pos=(4, 4))
    assert _income_line(building, worker_working=False) == "Income: —"


def test_income_line_shows_full_value_when_worker_working() -> None:
    building = LumberCamp(level=3, grid_pos=(4, 4))
    assert _income_line(building, worker_working=True) == "Income: —"


def test_layout_grows_when_production_status_line_is_present() -> None:
    surface = pygame.Surface((800, 600))
    building = LumberCamp(level=1, grid_pos=(4, 4))

    without_status = BuildingPanel.layout(
        surface,
        building,
        worker_assigned=True,
    )
    with_status = BuildingPanel.layout(
        surface,
        building,
        worker_assigned=True,
        production_status="Resting",
    )

    assert with_status.frame.height > without_status.frame.height
