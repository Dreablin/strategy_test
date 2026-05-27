"""Top-bar Research button refresh after Laboratory lifecycle (T435)."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import complete_construction
from game.input import GameInput
from game.ui.placement import PlacementController
from game.ui.top_bar import TopBar, research_button_visible
from game.camera import Camera
from game.world import World
from game.workers import WorkerManager


def _setup_input() -> tuple[GameInput, pygame.Surface, BuildingRegistry, WorkerManager]:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=60)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    workers = WorkerManager(registry)
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, workers, camera)
    return inp, surface, registry, workers


def _top_bar_layout(registry: BuildingRegistry, surface: pygame.Surface):
    return TopBar.layout(
        surface,
        current_population=0,
        max_population=4,
        show_research_button=research_button_visible(registry),
    )


def test_research_button_hidden_until_laboratory_construction_completes() -> None:
    _, surface, registry, _ = _setup_input()
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    assert laboratory.is_under_construction
    assert research_button_visible(registry) is False
    assert _top_bar_layout(registry, surface).research_button is None
    site = laboratory.construction_site
    assert site is not None
    for resource, amount in site.required_resources.items():
        site.delivered_resources[resource] = amount
    site.build_started_ms = 0
    site.build_time_ms = 1
    assert complete_construction(laboratory, 1_000)
    assert research_button_visible(registry) is True
    assert _top_bar_layout(registry, surface).research_button is not None


def test_demolishing_laboratory_hides_research_button() -> None:
    _, surface, registry, workers = _setup_input()
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    assert _top_bar_layout(registry, surface).research_button is not None
    registry.demolish(laboratory, workers)
    assert research_button_visible(registry) is False
    assert _top_bar_layout(registry, surface).research_button is None


def test_research_screen_closes_when_laboratory_demolished() -> None:
    inp, surface, registry, workers = _setup_input()
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    layout = _top_bar_layout(registry, surface)
    assert layout.research_button is not None
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=layout.research_button.center,
        ),
    )
    assert inp.research_screen_open is True
    registry.demolish(laboratory, workers)
    inp.handle(surface, pygame.event.Event(pygame.MOUSEMOTION, pos=(0, 0)))
    assert inp.research_screen_open is False


def test_rebuilt_laboratory_shows_research_button_again() -> None:
    _, surface, registry, workers = _setup_input()
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    registry.demolish(laboratory, workers)
    assert research_button_visible(registry) is False
    rebuilt = registry.place(Laboratory, near_town_hall_tile(12, 12))
    rebuilt.construction_site = None
    assert research_button_visible(registry) is True
    assert _top_bar_layout(registry, surface).research_button is not None
