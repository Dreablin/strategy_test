"""School panel: hire rows and click actions."""

import pygame

from game.buildings.school import School
from game.resources import ResourceManager
from game.ui.school_panel import SchoolPanel


def test_school_panel_hire_click_returns_worker_action() -> None:
    surface = pygame.Surface((900, 700))
    resources = ResourceManager()
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)
    worker_type, rect = layout.hire_buttons[0]
    assert (
        SchoolPanel.click_action(surface, rect.center, school, resources, worker_assigned=False)
        == f"hire:{worker_type}"
    )


def test_school_panel_demolish_click_returns_demolish() -> None:
    surface = pygame.Surface((900, 700))
    resources = ResourceManager()
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)
    assert SchoolPanel.click_action(surface, layout.demolish.center, school, resources, worker_assigned=False) == "demolish"
