"""School advanced-tab SCIENTIST hiring tests (T401)."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import town_hall_origin_tile
from game.ui.school_panel import SchoolPanel
from game.worker_tiers import worker_tier
from game.workers import WorkerManager
from game.world import World


def test_scientist_tier_is_advanced_for_school_filtering() -> None:
    assert worker_tier("SCIENTIST") == "advanced"


def test_scientist_appears_in_school_advanced_tab() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="advanced")
    worker_types = [worker_type for worker_type, _ in layout.hire_buttons]
    assert "SCIENTIST" in worker_types
    assert "WINEMAKER" in worker_types


def test_scientist_not_in_school_basic_tab() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    worker_types = [worker_type for worker_type, _ in layout.hire_buttons]
    assert "SCIENTIST" not in worker_types


def test_school_panel_click_scientist_returns_hire_action() -> None:
    registry = BuildingRegistry(World(world_seed=0))
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.construction_site = None
    school = registry.place(School, (15, 15))
    school.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    surface = pygame.Surface((900, 700))
    layout = SchoolPanel.layout(
        surface,
        school,
        worker_assigned=False,
        worker_manager=workers,
        tier="advanced",
    )
    scientist_rect = next(rect for worker_type, rect in layout.hire_buttons if worker_type == "SCIENTIST")
    action = SchoolPanel.click_action(
        surface,
        scientist_rect.center,
        school,
        worker_assigned=False,
        worker_manager=workers,
        tier="advanced",
    )
    assert action == "hire:SCIENTIST"


def test_school_enqueue_scientist_training() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.can_enqueue_training()
    assert school.enqueue_training("SCIENTIST")
    queue = school.training_queue()
    assert len(queue) == 1
    assert queue[0].type_tag == "SCIENTIST"
