"""Tests for WINEMAKER as an advanced hireable worker (T343)."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import town_hall_origin_tile
from game.ui.school_panel import SchoolPanel
from game.worker_hiring import HIRABLE_WORKERS
from game.worker_tiers import worker_tier, workers_of_tier
from game.workers import WorkerManager
from game.world import World


def test_winemaker_is_in_hirable_workers() -> None:
    assert "WINEMAKER" in HIRABLE_WORKERS


def test_winemaker_tier_is_advanced() -> None:
    assert worker_tier("WINEMAKER") == "advanced"


def test_winemaker_in_workers_of_advanced_tier() -> None:
    assert "WINEMAKER" in workers_of_tier("advanced")


def test_winemaker_not_in_basic_tier() -> None:
    assert "WINEMAKER" not in workers_of_tier("basic")


def test_winemaker_appears_in_school_advanced_tab() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="advanced")
    worker_types = [wt for wt, _ in layout.hire_buttons]
    assert "WINEMAKER" in worker_types


def test_winemaker_not_in_school_basic_tab() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    worker_types = [wt for wt, _ in layout.hire_buttons]
    assert "WINEMAKER" not in worker_types


def test_winemaker_can_be_hired_via_worker_manager() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, (15, 15))
    school.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    worker = workers.hire("WINEMAKER")
    assert worker is not None
    assert worker.type_tag == "WINEMAKER"


def test_winemaker_training_queue_in_school() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.can_enqueue_training()
    assert school.enqueue_training("WINEMAKER")
    queue = school.training_queue()
    assert len(queue) == 1
    assert queue[0].type_tag == "WINEMAKER"
