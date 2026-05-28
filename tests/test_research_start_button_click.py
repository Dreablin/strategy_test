"""Research screen Start button click tests (T422)."""

from __future__ import annotations

import pygame

from game.input import GameInput
from game.research_eligibility import research_ui_eligibility
from game.ui.research_screen import ResearchScreen
from game.ui.top_bar import TopBar
from tests.test_research_screen import _input_with_completed_laboratory


def _open_research_screen(inp: GameInput, surface: pygame.Surface) -> None:
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


def test_click_start_research_id_returns_enabled_tile_only() -> None:
    surface = pygame.Surface((1280, 720))
    layout = ResearchScreen.layout(surface)
    tile1 = next(t for t in layout.content.tiles if t.research_id == "1")
    tile2 = next(t for t in layout.content.tiles if t.research_id == "2")
    can_start = {"1": True, "2": False}
    assert (
        ResearchScreen.click_start_research_id(
            surface, tile1.start_button.center, research_can_start=can_start
        )
        == "1"
    )
    assert (
        ResearchScreen.click_start_research_id(
            surface, tile2.start_button.center, research_can_start=can_start
        )
        is None
    )


def test_game_input_start_button_starts_active_research() -> None:
    inp, surface, registry = _input_with_completed_laboratory()
    _open_research_screen(inp, surface)
    layout = ResearchScreen.layout(surface)
    tile1 = next(t for t in layout.content.tiles if t.research_id == "1")
    can_start, _ = research_ui_eligibility(research_state=inp.research_state, registry=registry)
    assert can_start["1"] is True
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=tile1.start_button.center,
        ),
    )
    assert inp.research_state.active_research_id() == "1"
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    assert laboratory.has_research_input_storage()
    assert inp.research_screen_open is True


def test_disabled_start_button_click_does_not_start_research() -> None:
    inp, surface, registry = _input_with_completed_laboratory()
    _open_research_screen(inp, surface)
    layout = ResearchScreen.layout(surface)
    tile2 = next(t for t in layout.content.tiles if t.research_id == "2")
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=tile2.start_button.center,
        ),
    )
    assert inp.research_state.active_research_id() is None
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    assert not laboratory.has_research_input_storage()


def test_second_start_while_active_is_ignored() -> None:
    inp, surface, registry = _input_with_completed_laboratory()
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    laboratory.level = 10
    _open_research_screen(inp, surface)
    layout = ResearchScreen.layout(surface)
    tile1 = next(t for t in layout.content.tiles if t.research_id == "1")
    tile2 = next(t for t in layout.content.tiles if t.research_id == "2")
    for pos in (tile1.start_button.center, tile2.start_button.center):
        inp.handle(
            surface,
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=pos,
            ),
        )
    assert inp.research_state.active_research_id() == "1"
