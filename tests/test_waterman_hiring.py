"""Tests for hireable WATERMAN worker (T279)."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.ui.school_panel import SchoolPanel
from game.world import World
from game.worker_hiring import HIRABLE_WORKERS, WORKER_TO_BUILDING
from game.worker_models import Worker
from game.worker_satiety import MAX_WORKER_SATIETY
from game.workers import WorkerManager


def test_waterman_maps_to_well_in_worker_to_building() -> None:
    assert WORKER_TO_BUILDING["WATERMAN"] == "WELL"


def test_waterman_is_hirable_worker_type() -> None:
    assert "WATERMAN" in HIRABLE_WORKERS


def test_school_panel_includes_waterman_hire_tile() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    types = [wt for wt, _ in layout.hire_buttons]
    assert "WATERMAN" in types


def test_waterman_training_enqueue_and_cancel() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("WATERMAN")
    assert school.training_queue()[0].type_tag == "WATERMAN"
    assert school.cancel_training_at(0)
    assert len(school.training_queue()) == 0


def test_worker_waterman_starts_at_full_satiety() -> None:
    w = Worker("WATERMAN")
    assert w.satiety == MAX_WORKER_SATIETY


def test_hired_waterman_starts_at_full_satiety() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)
    hired = wm.hire("WATERMAN", source_building=school)
    assert hired is not None
    assert hired.satiety == MAX_WORKER_SATIETY


def test_reassign_all_assigns_idle_waterman_to_empty_well() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(12, 8))
    well.construction_site = None
    wm = WorkerManager(registry)
    waterman = Worker("WATERMAN", stand_tile=near_town_hall_tile(6, 8))
    wm.add_worker(waterman)
    wm.reassign_all()
    assert waterman.assigned_building is well
