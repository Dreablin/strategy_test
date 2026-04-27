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
    assert layout.upgrade is not None


def test_hire_buttons_disabled_when_food_below_cost() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    assert resources.try_spend({"food": 200})
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    assert not any(layout.hire_enabled.values())
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
    worker_type, rect = layout.hire_buttons[0]
    assert (
        TownHallPanel.click_action(surface, rect.center, town_hall, resources, worker_assigned=False)
        == f"hire:{worker_type}"
    )


def test_hire_click_for_locked_worker_type_returns_none() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    stone_rect = next(r for w, r in layout.hire_buttons if w == "STONECUTTER")
    assert (
        TownHallPanel.click_action(surface, stone_rect.center, town_hall, resources, worker_assigned=False) is None
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


def test_hire_buttons_are_inside_panel_and_non_overlapping() -> None:
    surface = pygame.Surface((800, 600))
    resources = ResourceManager()
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    rects = [rect for _w, rect in layout.hire_buttons]
    assert rects
    for rect in rects:
        assert layout.frame.contains(rect)
    for i in range(len(rects) - 1):
        assert rects[i].bottom <= rects[i + 1].top


def test_town_hall_upgrade_cost_formatting() -> None:
    assert TownHallPanel._format_cost({"wood": 5}) == "5 wood"
    assert TownHallPanel._format_cost({"wood": 5, "stone": 5}) == "5 wood, 5 stone"
