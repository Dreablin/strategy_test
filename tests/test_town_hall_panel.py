"""Town Hall panel UI: hire section visibility and disabled/active clicks."""

import pygame

from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.ui.town_hall_panel import TownHallPanel


def test_town_hall_panel_layout_has_four_hire_buttons() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    assert len(layout.hire_buttons) == 4


def test_hire_buttons_disabled_when_food_below_cost() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    assert resources.try_spend({"food": 200})
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    assert not layout.hire_enabled
    _, first = layout.hire_buttons[0]
    assert (
        TownHallPanel.click_action(surface, first.center, town_hall, resources, worker_assigned=False)
        is None
    )


def test_hire_click_returns_worker_type_when_affordable() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    worker_type, rect = layout.hire_buttons[2]
    assert (
        TownHallPanel.click_action(surface, rect.center, town_hall, resources, worker_assigned=False)
        == f"hire:{worker_type}"
    )


def test_town_hall_panel_close_button_action() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    assert (
        TownHallPanel.click_action(surface, layout.close.center, town_hall, resources, worker_assigned=False)
        == "close"
    )


def test_town_hall_panel_draw_smoke() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    TownHallPanel.draw(surface, town_hall, resources, worker_assigned=False)
    assert surface.get_at((400, 300)) != (0, 0, 0, 255)
