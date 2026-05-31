"""Research screen open/close shell tests (T409)."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.lumber_camp import LumberCamp
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.input import GameInput
from game.laboratory_visibility import has_completed_laboratory
from game.ui.placement import PlacementController
from game.ui.research_screen import ResearchScreen
from game.ui.top_bar import TopBar
from game.camera import Camera
from game.world import World
from game.workers import WorkerManager


def _input_with_completed_laboratory() -> tuple[GameInput, pygame.Surface, BuildingRegistry]:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    camera = Camera()
    workers = WorkerManager(registry)
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, workers, camera)
    assert has_completed_laboratory(registry)
    return inp, surface, registry


def test_research_screen_labels_en() -> None:
    assert ResearchScreen.screen_title() == "Research"
    assert ResearchScreen.technology_label() == "Technology"
    assert ResearchScreen.tier_label(2) == "Tier 2"


def test_research_screen_labels_ru(use_locale) -> None:
    with use_locale("ru"):
        assert ResearchScreen.screen_title() == "Исследования"
        assert ResearchScreen.technology_label() == "Технологии"
        assert ResearchScreen.tier_label(2) == "Уровень 2"


def test_research_screen_layout_covers_surface() -> None:
    surface = pygame.Surface((800, 600))
    layout = ResearchScreen.layout(surface)
    assert layout.overlay.size == surface.get_size()
    assert layout.frame.size == surface.get_size()
    assert layout.close.collidepoint(layout.close.center)


def test_research_screen_draw_smoke() -> None:
    surface = pygame.Surface((800, 600))
    ResearchScreen.draw(surface)
    bg = (28, 32, 40)
    title_region = pygame.Rect(16, 16, 200, 44)
    assert any(
        surface.get_at((x, y))[:3] != bg
        for y in range(title_region.top, title_region.bottom)
        for x in range(title_region.left, title_region.right)
    )


def test_research_screen_close_click() -> None:
    surface = pygame.Surface((800, 600))
    layout = ResearchScreen.layout(surface)
    assert ResearchScreen.click_action(surface, layout.close.center) == "close"
    assert ResearchScreen.click_action(surface, layout.frame.center) == "inside"


def test_research_button_opens_research_screen() -> None:
    inp, surface, _ = _input_with_completed_laboratory()
    layout = TopBar.layout(
        surface,
        current_population=0,
        max_population=4,
        show_research_button=True,
    )
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
    assert inp.panel_building is None
    assert inp.population_panel_open is False


def test_escape_closes_research_screen() -> None:
    inp, surface, _ = _input_with_completed_laboratory()
    layout = TopBar.layout(
        surface,
        current_population=0,
        max_population=4,
        show_research_button=True,
    )
    assert layout.research_button is not None
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=layout.research_button.center,
        ),
    )
    inp.handle(surface, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert inp.research_screen_open is False


def test_close_button_closes_research_screen() -> None:
    inp, surface, _ = _input_with_completed_laboratory()
    layout = TopBar.layout(
        surface,
        current_population=0,
        max_population=4,
        show_research_button=True,
    )
    assert layout.research_button is not None
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=layout.research_button.center,
        ),
    )
    screen_layout = ResearchScreen.layout(surface)
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=screen_layout.close.center,
        ),
    )
    assert inp.research_screen_open is False


def test_research_screen_open_absorbs_map_clicks() -> None:
    inp, surface, registry = _input_with_completed_laboratory()
    camp = registry.place(LumberCamp, near_town_hall_tile(20, 20))
    camp.construction_site = None
    top = TopBar.layout(
        surface,
        current_population=0,
        max_population=4,
        show_research_button=True,
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
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=surface.get_rect().center,
        ),
    )
    assert inp.research_screen_open is True
    assert inp.panel_building is None
    assert camp in registry.all()
