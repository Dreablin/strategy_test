"""Failing housing-domain tests for Phase 15 (T161)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.house import House
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.construction import complete_construction
from game.config import building_level_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.housing import current_population, housing_house, housing_town_hall, max_population
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


def test_housing_town_hall_uses_building_settings() -> None:
    for level in (1, 5, 10):
        assert housing_town_hall(level) == building_level_int_setting("TOWN_HALL", "housing", level)


def test_housing_house_uses_building_settings() -> None:
    for level in (1, 4, 10):
        assert housing_house(level) == building_level_int_setting("HOUSE", "housing", level)


def test_max_population_sums_town_hall_and_houses_only() -> None:
    reg = _Registry(
        buildings=[
            _B("TOWN_HALL", 3),
            _B("HOUSE", 2),
            _B("HOUSE", 5),
            _B("SCHOOL", 7),  # ignored
        ]
    )
    expected = housing_town_hall(3) + housing_house(2) + housing_house(5)
    assert max_population(reg, 0) == expected


def test_max_population_accepts_worker_manager_or_count_without_hidden_globals() -> None:
    reg = _Registry(buildings=[_B("TOWN_HALL", 1), _B("HOUSE", 1)])
    expected = housing_town_hall(1) + housing_house(1)
    assert max_population(reg, 2) == expected
    assert max_population(reg, _Workers(2)) == expected


def test_house_under_initial_construction_does_not_increase_population_cap() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())

    house = registry.place(House, near_town_hall_tile(8, 8))

    assert house.is_under_construction
    assert max_population(registry, 0) == housing_town_hall(1)

    site = house.construction_site
    assert site is not None
    site.delivered_resources = dict(site.required_resources)
    site.build_started_ms = 1_000
    assert complete_construction(house, 1_000 + site.build_time_ms)

    assert max_population(registry, 0) == housing_town_hall(1) + housing_house(1)


def test_house_upgrade_preserves_current_population_cap_until_complete() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    house = registry.place(House, near_town_hall_tile(8, 8))
    house.construction_site = None

    assert max_population(registry, 0) == housing_town_hall(1) + housing_house(1)
    assert registry.upgrade_building(house)

    assert house.is_under_construction
    assert house.level == 1
    assert max_population(registry, 0) == housing_town_hall(1) + housing_house(1)

    site = house.construction_site
    assert site is not None
    site.delivered_resources = dict(site.required_resources)
    site.build_started_ms = 1_000
    assert complete_construction(house, 1_000 + site.build_time_ms)

    assert house.level == 2
    assert max_population(registry, 0) == housing_town_hall(1) + housing_house(2)


def test_current_population_counts_spawned_workers_plus_school_queue() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    workers = WorkerManager(registry)
    workers.add_worker(Worker("LUMBERJACK"))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")
    assert current_population(registry, workers) == 3


def test_hire_is_safe_noop_when_housing_cap_reached() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    workers = WorkerManager(registry)
    cap = housing_town_hall(1)

    for _ in range(cap):
        assert workers.hire("LUMBERJACK") is not None
    assert len(workers.workers()) == cap
    assert workers.hire("LUMBERJACK") is None
    assert len(workers.workers()) == cap


def test_school_panel_disables_hire_when_housing_cap_reached() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    workers = WorkerManager(registry)
    for _ in range(housing_town_hall(1)):
        assert workers.hire("LUMBERJACK", source_building=school) is not None

    surface = pygame.Surface((900, 700))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, worker_manager=workers)
    worker_type, button = layout.hire_buttons[0]
    assert layout.hire_enabled[worker_type] is False
    assert (
        SchoolPanel.click_action(
            surface,
            button.center,
            school,
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
    workers = WorkerManager(registry)
    cap = housing_town_hall(1)

    for _ in range(cap - 1):
        workers.add_worker(Worker("LUMBERJACK"))
    assert current_population(registry, workers) == cap - 1
    assert workers.can_hire("LUMBERJACK", charge_cost=False) is True

    assert school.enqueue_training("LUMBERJACK")
    assert current_population(registry, workers) == cap
    assert workers.can_hire("LUMBERJACK", charge_cost=False) is False

    assert school.cancel_training_at(0) is True
    assert current_population(registry, workers) == cap - 1
    assert workers.can_hire("LUMBERJACK", charge_cost=False) is True
