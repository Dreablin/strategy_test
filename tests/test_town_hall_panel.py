"""Town Hall panel UI: upgrade/close actions without hiring."""

import pygame

from game.buildings.town_hall import TownHall
from game.ui import town_hall_panel
from game.ui.town_hall_panel import TownHallPanel


def test_town_hall_panel_layout_has_no_hire_buttons() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.hire_buttons == ()
    assert layout.upgrade is not None


def test_town_hall_panel_click_inside_without_buttons_returns_none() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    pos = (layout.frame.left + 20, layout.frame.bottom - 20)
    assert TownHallPanel.click_action(surface, pos, town_hall, worker_assigned=False) is None


def test_town_hall_panel_close_button_action() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert (
        TownHallPanel.click_action(surface, layout.close.center, town_hall, worker_assigned=False)
        == "close"
    )


def test_town_hall_panel_draw_smoke() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    TownHallPanel.draw(surface, town_hall, worker_assigned=False)
    assert surface.get_at((400, 300)) != (0, 0, 0, 255)


def test_hire_buttons_removed_from_town_hall_panel() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.hire_buttons == ()


def test_town_hall_panel_has_secondary_storage_frame_and_click_is_non_closing() -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.storage_frame.left > layout.frame.right
    assert (
        TownHallPanel.click_action(
            surface,
            layout.storage_frame.center,
            town_hall,
            worker_assigned=False,
        )
        is None
    )


def test_town_hall_storage_rows_include_bread() -> None:
    keys = [key for key, _label in town_hall_panel._STORAGE_ROWS]  # noqa: SLF001
    assert "bread" in keys


def test_town_hall_upgrade_button_is_enabled_without_cost_checks() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.upgrade is not None
    assert layout.upgrade_enabled is True
