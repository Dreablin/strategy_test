"""Bounded end-to-end Laboratory and Research flow (T436)."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import complete_construction
from game.input import GameInput
from game.research_config import RESEARCH_BY_ID
from game.research_eligibility import research_ui_eligibility
from game.research_state import ResearchState
from game.research_technology_chain import (
    technology_start_eligibility,
    technology_unlocked_after_completing,
)
from game.ui.placement import PlacementController
from game.ui.research_screen import ResearchScreen
from game.ui.top_bar import TopBar, research_button_visible
from game.camera import Camera
from game.world import World
from game.workers import WorkerManager


def _integration_setup(
    *,
    laboratory_level: int = 3,
) -> tuple[GameInput, pygame.Surface, BuildingRegistry, WorkerManager, Laboratory, TownHall, ResearchState]:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=70)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    site = laboratory.construction_site
    assert site is not None
    for resource, amount in site.required_resources.items():
        site.delivered_resources[resource] = amount
    site.build_started_ms = 0
    site.build_time_ms = 1
    assert complete_construction(laboratory, 1_000)
    laboratory.level = laboratory_level
    state = ResearchState()
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, workers, camera, research_state=state)
    return inp, surface, registry, workers, laboratory, town_hall, state


def _open_research_screen(inp: GameInput, surface: pygame.Surface, registry: BuildingRegistry) -> None:
    assert research_button_visible(registry)
    top = TopBar.layout(
        surface,
        current_population=0,
        max_population=4,
        show_research_button=research_button_visible(registry),
    )
    assert top.research_button is not None
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=top.research_button.center,
        ),
    )
    assert inp.research_screen_open


def _click_start_research(
    inp: GameInput,
    surface: pygame.Surface,
    registry: BuildingRegistry,
    research_id: str,
) -> None:
    can_start, _ = research_ui_eligibility(
        research_state=inp.research_state,
        registry=registry,
    )
    layout = ResearchScreen.layout(surface)
    tile = next(t for t in layout.content.tiles if t.research_id == research_id)
    assert can_start[research_id] is True
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=tile.start_button.center,
        ),
    )


def _deliver_active_research_inputs(
    *,
    research_id: str,
    town_hall: TownHall,
    laboratory: Laboratory,
    workers: WorkerManager,
) -> None:
    definition = RESEARCH_BY_ID[research_id]
    for resource, amount in definition.resource_cost.items():
        town_hall.add_to_warehouse(resource, amount)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    for now_ms in range(0, 1_200_000, 500):
        workers.update(now_ms)
        if laboratory.all_research_inputs_delivered():
            break
    assert laboratory.all_research_inputs_delivered()


def _run_until_research_complete(
    workers: WorkerManager,
    laboratory: Laboratory,
    state: ResearchState,
    research_id: str,
) -> None:
    if workers.laboratory_research_contributing_scientist_count(laboratory) < 1:
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        workers.assign_to_building(scientist, laboratory)
    required = RESEARCH_BY_ID[research_id].required_points
    rate = laboratory.research_points_per_scientist_per_second()
    ticks_needed = (required + rate - 1) // rate + 2
    workers.update(0)
    for step in range(1, ticks_needed + 1):
        workers.update(step * 1_000)
        if state.is_completed(research_id):
            return
    raise AssertionError(f"research {research_id!r} did not complete in time")


def test_laboratory_research_end_to_end_unlocks_next_technology() -> None:
    inp, surface, registry, workers, laboratory, town_hall, state = _integration_setup(
        laboratory_level=3,
    )
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None
    workers.assign_to_building(scientist, laboratory)
    assert workers.laboratory_research_contributing_scientist_count(laboratory) == 1

    _open_research_screen(inp, surface, registry)
    _click_start_research(inp, surface, registry, "1")
    assert state.active_research_id() == "1"
    assert laboratory.has_research_input_storage()

    _deliver_active_research_inputs(
        research_id="1",
        town_hall=town_hall,
        laboratory=laboratory,
        workers=workers,
    )
    _run_until_research_complete(workers, laboratory, state, "1")

    assert state.is_completed("1")
    assert not state.has_active_research()
    assert not laboratory.has_research_input_storage()

    assert technology_unlocked_after_completing(
        "1", research_state=state, registry=registry
    ) == "2"
    tech2 = technology_start_eligibility("2", research_state=state, registry=registry)
    assert tech2.can_start is True
    assert tech2.lock_reason is None
    can_start, _ = research_ui_eligibility(research_state=state, registry=registry)
    assert can_start["2"] is True
