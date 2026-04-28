"""Phase 15 headless smoke for school queues and housing gate."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.resources import ResourceManager
from game.ui.school_panel import SchoolPanel
from game.world import World
from game.workers import Worker, WorkerManager


def test_smoke_phase15_school_queue_housing_gate_and_independent_schools() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school_a = registry.place(School, near_town_hall_tile(8, 8))
    school_b = registry.place(School, near_town_hall_tile(18, 8))
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)

    # Fill close to Town Hall cap (8), then queue trainees.
    for _ in range(6):
        workers.add_worker(Worker("LUMBERJACK"))
    assert len(workers.workers()) == 6

    assert school_a.enqueue_training("LUMBERJACK")
    assert school_a.enqueue_training("FARMER")
    assert school_b.enqueue_training("LUMBERJACK")

    # Queued trainees reserve population slots; only one completion can spawn at cap.
    workers.update(30_000)
    assert len(workers.workers()) == 7
    assert len(school_a.training_queue()) == 1
    assert len(school_b.training_queue()) == 0
    assert school_a.training_progress_ms() == 0

    # At cap, school panel blocks enqueueing an additional trainee.
    layout = SchoolPanel.layout(
        surface,
        school_a,
        resources,
        worker_assigned=False,
        worker_manager=workers,
    )
    worker_type, button = layout.hire_buttons[0]
    assert layout.hire_enabled[worker_type] is False
    assert (
        SchoolPanel.click_action(
            surface,
            button.center,
            school_a,
            resources,
            worker_assigned=False,
            worker_manager=workers,
        )
        is None
    )
