"""RED tests for hireable COOK worker (T252)."""

from __future__ import annotations

import pygame

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_satiety import MAX_WORKER_SATIETY
from game.ui.school_panel import SchoolPanel
from game.world import World
from game.worker_hiring import HIRABLE_WORKERS, WORKER_TO_BUILDING
from game.worker_models import Worker
from game.workers import WorkerManager


def _assert_nonempty_surface(surf: pygame.Surface) -> None:
    assert surf.get_width() > 0 and surf.get_height() > 0
    found = False
    for x in range(0, surf.get_width(), max(1, surf.get_width() // 4)):
        for y in range(0, surf.get_height(), max(1, surf.get_height() // 4)):
            c = surf.get_at((x, y))
            a = c.a if hasattr(c, "a") else c[3]
            if a > 0 and sum(c[:3]) > 0:
                found = True
                break
        if found:
            break
    assert found


def test_cook_maps_to_canteen_in_worker_to_building() -> None:
    assert WORKER_TO_BUILDING["COOK"] == "CANTEEN"


def test_cook_is_hirable_worker_type() -> None:
    assert "COOK" in HIRABLE_WORKERS


def test_school_panel_includes_cook_hire_tile() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    types = [wt for wt, _ in layout.hire_buttons]
    assert "COOK" in types


def test_school_panel_cook_hire_click_returns_hire_action() -> None:
    surface = pygame.Surface((900, 700))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, worker_manager=wm)
    cook_button = next(rect for worker_type, rect in layout.hire_buttons if worker_type == "COOK")
    assert (
        SchoolPanel.click_action(
            surface,
            cook_button.center,
            school,
            worker_assigned=False,
            worker_manager=wm,
        )
        == "hire:COOK"
    )


def test_cook_training_enqueue_and_cancel() -> None:
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("COOK")
    assert school.training_queue()[0].type_tag == "COOK"
    assert school.cancel_training_at(0)
    assert len(school.training_queue()) == 0


def test_worker_cook_starts_at_full_satiety() -> None:
    cook = Worker("COOK")
    assert cook.satiety == MAX_WORKER_SATIETY


def test_hired_cook_starts_at_full_satiety() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)
    hired = wm.hire("COOK", source_building=school)
    assert hired is not None
    assert hired.satiety == MAX_WORKER_SATIETY


def test_cook_worker_dot_and_ui_icons_fallback_smoke() -> None:
    from game.assets import hire_ui_icon, worker_dot, worker_ui_icon

    _assert_nonempty_surface(worker_dot("COOK"))
    _assert_nonempty_surface(worker_ui_icon("COOK"))
    _assert_nonempty_surface(hire_ui_icon("COOK"))


def test_reassign_all_assigns_idle_cook_to_empty_canteen() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(12, 8))
    canteen.construction_site = None
    wm = WorkerManager(registry)
    cook = Worker("COOK", stand_tile=near_town_hall_tile(6, 8))
    wm.add_worker(cook)
    wm.reassign_all()
    assert cook.assigned_building is canteen
