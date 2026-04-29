"""School panel: hire rows and click actions."""

import pygame

from game.buildings.school import SCHOOL_TRAINING_MS
from game.buildings.school import School
from game.ui.school_panel import SchoolPanel


def test_school_panel_hire_click_returns_worker_action() -> None:
    surface = pygame.Surface((900, 700))
    resources = None
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)
    worker_type, rect = layout.hire_buttons[0]
    assert (
        SchoolPanel.click_action(surface, rect.center, school, resources, worker_assigned=False)
        == f"hire:{worker_type}"
    )


def test_school_panel_demolish_click_returns_demolish() -> None:
    surface = pygame.Surface((900, 700))
    resources = None
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)
    assert SchoolPanel.click_action(surface, layout.demolish.center, school, resources, worker_assigned=False) == "demolish"


def test_school_panel_layout_contains_seven_training_slots() -> None:
    surface = pygame.Surface((900, 700))
    resources = None
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)
    assert len(layout.queue_slots) == 7
    assert any(worker_type == "CARRIER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "BUILDER" for worker_type, _ in layout.hire_buttons)
    assert layout.hire_buttons[0][0] == "CARRIER"
    assert layout.hire_buttons[1][0] == "BUILDER"


def test_school_panel_draws_yellow_progress_for_active_training_slot() -> None:
    surface = pygame.Surface((900, 700))
    resources = None
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    school.update_training(SCHOOL_TRAINING_MS // 2)
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)

    SchoolPanel.draw(surface, school, resources, worker_assigned=False)

    slot = layout.queue_slots[0]
    found_yellow = False
    for x in range(slot.left, slot.right):
        pixel = surface.get_at((x, slot.bottom - 3))
        if pixel.r > 180 and pixel.g > 180 and pixel.b < 120:
            found_yellow = True
            break
    assert found_yellow


def test_school_panel_clicking_queue_slot_returns_cancel_action() -> None:
    surface = pygame.Surface((900, 700))
    resources = None
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False)

    assert SchoolPanel.click_action(surface, layout.queue_slots[0].center, school, resources, worker_assigned=False) == "cancel:0"
    assert SchoolPanel.click_action(surface, layout.queue_slots[1].center, school, resources, worker_assigned=False) == "cancel:1"
    assert SchoolPanel.click_action(surface, layout.queue_slots[2].center, school, resources, worker_assigned=False) is None
