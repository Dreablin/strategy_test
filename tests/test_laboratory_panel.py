"""Laboratory panel scientist slot display tests (T407)."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_config import RESEARCH_BY_ID
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.ui.laboratory_panel import (
    LaboratoryPanel,
    scientist_slot_states,
    scientist_slots_summary,
)
from game.workers import WorkerManager
from game.world import World


def _built_laboratory(*, level: int) -> tuple[Laboratory, WorkerManager]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return laboratory, workers


def test_laboratory_panel_supports_building() -> None:
    laboratory = Laboratory(level=1, grid_pos=(4, 4))
    assert LaboratoryPanel.supports_building(laboratory) is True
    assert laboratory.active is True
    laboratory.set_active(False)
    assert laboratory.active is False


def test_scientist_slot_states_reflect_active_count() -> None:
    assert scientist_slot_states(3, ()) == (False, False, False)
    assert scientist_slot_states(3, [object(), object()]) == (True, True, False)
    assert scientist_slots_summary(active_count=2, capacity=5) == "Scientists: 2 / 5"


def test_layout_has_one_tile_per_scientist_slot() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=3)
    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="No worker",
        worker_manager=workers,
    )
    assert len(layout.scientist_tiles) == laboratory.scientist_slot_capacity() == 2
    assert len(layout.scientist_slot_states) == 2
    assert layout.scientist_slot_states == (False, False)


def test_layout_marks_filled_slots_when_scientists_active() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=5)
    for _ in range(2):
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        workers.assign_to_building(scientist, laboratory)
    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=True,
        production_status="Ready",
        worker_manager=workers,
    )
    assert layout.scientist_slot_states == (True, True, False)
    assert sum(layout.scientist_slot_states) == workers.laboratory_research_contributing_scientist_count(laboratory)


def test_layout_does_not_mark_walking_scientist_as_inside() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=3)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None
    workers.reassign_all()

    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=True,
        production_status="On the way",
        worker_manager=workers,
    )

    assert scientist.assigned_building is laboratory
    assert workers.laboratory_active_scientist_count(laboratory) == 1
    assert workers.laboratory_research_contributing_scientist_count(laboratory) == 0
    assert layout.scientist_slot_states == (False, False)


def test_draw_distinguishes_assigned_and_empty_slot_pixels() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=3)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None
    workers.assign_to_building(scientist, laboratory)
    layout = LaboratoryPanel.draw(
        surface,
        laboratory,
        worker_assigned=True,
        production_status="Ready",
        worker_manager=workers,
    )
    assigned_tile = layout.scientist_tiles[0]
    empty_tile = layout.scientist_tiles[1]
    assigned_color = surface.get_at((assigned_tile.left + 4, assigned_tile.top + 4))
    empty_color = surface.get_at((empty_tile.left + 4, empty_tile.top + 4))
    assert assigned_color != empty_color
    assert assigned_color[0] > empty_color[0]


def test_panel_close_and_demolish_clicks() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=1)
    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="No worker",
        worker_manager=workers,
    )
    assert (
        LaboratoryPanel.click_action(
            surface,
            layout.close.center,
            laboratory,
            worker_assigned=False,
            worker_manager=workers,
        )
        == "close"
    )
    assert layout.demolish is not None
    assert (
        LaboratoryPanel.click_action(
            surface,
            layout.demolish.center,
            laboratory,
            worker_assigned=False,
            worker_manager=workers,
        )
        == "demolish"
    )


def test_laboratory_panel_toggle_click_and_label_pixels() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=1)
    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="Ready",
        worker_manager=workers,
    )

    assert (
        LaboratoryPanel.click_action(
            surface,
            layout.toggle.center,
            laboratory,
            worker_assigned=False,
            production_status="Ready",
            worker_manager=workers,
        )
        == "toggle_active"
    )

    laboratory.set_active(False)
    drawn = LaboratoryPanel.draw(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="Inactive",
        worker_manager=workers,
    )
    assert surface.get_at(drawn.toggle.center)[:3] != (0, 0, 0)


def test_click_inside_scientist_tile_does_not_close_panel() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=1)
    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="No worker",
        worker_manager=workers,
    )
    assert (
        LaboratoryPanel.click_action(
            surface,
            layout.scientist_tiles[0].center,
            laboratory,
            worker_assigned=False,
            worker_manager=workers,
        )
        is None
    )


def test_laboratory_upgrade_disabled_while_research_active() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=1)
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=workers._registry)  # noqa: SLF001

    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="Ready",
        worker_manager=workers,
        research_state=state,
    )

    assert layout.upgrade is not None
    assert layout.upgrade_enabled is False
    assert (
        LaboratoryPanel.click_action(
            surface,
            layout.upgrade.center,
            laboratory,
            worker_assigned=False,
            production_status="Ready",
            worker_manager=workers,
            research_state=state,
        )
        is None
    )


def test_laboratory_upgrade_reenabled_after_research_completes() -> None:
    surface = pygame.Surface((1280, 720))
    laboratory, workers = _built_laboratory(level=1)
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=workers._registry)  # noqa: SLF001
    for resource in laboratory.research_input_resources():
        laboratory.add_research_input(resource, laboratory.research_input_capacity(resource))
        state.add_delivered(resource, laboratory.research_input_capacity(resource))
    state.add_points(RESEARCH_BY_ID["1"].required_points)
    state.mark_research_completed("1")

    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="Ready",
        worker_manager=workers,
        research_state=state,
    )

    assert layout.upgrade is not None
    assert layout.upgrade_enabled is True
    assert (
        LaboratoryPanel.click_action(
            surface,
            layout.upgrade.center,
            laboratory,
            worker_assigned=False,
            production_status="Ready",
            worker_manager=workers,
            research_state=state,
        )
        == "upgrade"
    )
