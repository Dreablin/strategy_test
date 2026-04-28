"""Failing housing-domain tests for Phase 15 (T161)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.housing import current_population, housing_house, housing_town_hall, max_population
from game.resources import ResourceManager
from game.ui.school_panel import SchoolPanel
from game.workers import Worker, WorkerManager
from game.world import World


@dataclass
class _B:
    type_tag: str
    level: int


@dataclass
class _Registry:
    buildings: list[_B]

    def all(self) -> list[_B]:
        return list(self.buildings)


@dataclass
class _Workers:
    count: int

    def workers(self) -> tuple[object, ...]:
        return tuple(object() for _ in range(self.count))


def test_housing_town_hall_formula() -> None:
    assert housing_town_hall(1) == 8
    assert housing_town_hall(5) == 16
    assert housing_town_hall(10) == 26


def test_housing_house_formula() -> None:
    assert housing_house(1) == 2
    assert housing_house(4) == 8
    assert housing_house(10) == 20


def test_max_population_sums_town_hall_and_houses_only() -> None:
    reg = _Registry(
        buildings=[
            _B("TOWN_HALL", 3),  # 12
            _B("HOUSE", 2),  # 4
            _B("HOUSE", 5),  # 10
            _B("SCHOOL", 7),  # ignored
        ]
    )
    assert max_population(reg, 0) == 26


def test_max_population_accepts_worker_manager_or_count_without_hidden_globals() -> None:
    reg = _Registry(buildings=[_B("TOWN_HALL", 1), _B("HOUSE", 1)])
    assert max_population(reg, 2) == 10
    assert max_population(reg, _Workers(2)) == 10


def test_current_population_counts_spawned_workers_plus_school_queue() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    workers.add_worker(Worker("LUMBERJACK"))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")
    assert current_population(registry, workers) == 3


def test_hire_is_safe_noop_when_housing_cap_reached() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    resources = ResourceManager()
    resources.add("food", 10_000)
    workers = WorkerManager(resources, registry)

    for _ in range(8):
        assert workers.hire("LUMBERJACK") is not None
    assert len(workers.workers()) == 8
    assert workers.hire("LUMBERJACK") is None
    assert len(workers.workers()) == 8


def test_school_panel_disables_hire_when_housing_cap_reached() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    resources = ResourceManager()
    resources.add("food", 10_000)
    workers = WorkerManager(resources, registry)
    for _ in range(8):
        assert workers.hire("LUMBERJACK", source_building=school) is not None

    surface = pygame.Surface((900, 700))
    layout = SchoolPanel.layout(surface, school, resources, worker_assigned=False, worker_manager=workers)
    worker_type, button = layout.hire_buttons[0]
    assert layout.hire_enabled[worker_type] is False
    assert (
        SchoolPanel.click_action(
            surface,
            button.center,
            school,
            resources,
            worker_assigned=False,
            worker_manager=workers,
        )
        is None
    )


def test_enqueue_reserves_population_and_cancel_releases_population() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)

    for _ in range(7):
        workers.add_worker(Worker("LUMBERJACK"))
    assert current_population(registry, workers) == 7
    assert workers.can_hire("LUMBERJACK", charge_cost=False) is True

    assert school.enqueue_training("LUMBERJACK")
    assert current_population(registry, workers) == 8
    assert workers.can_hire("LUMBERJACK", charge_cost=False) is False

    assert school.cancel_training_at(0) is True
    assert current_population(registry, workers) == 7
    assert workers.can_hire("LUMBERJACK", charge_cost=False) is True
