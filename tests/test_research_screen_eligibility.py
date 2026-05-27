"""Research screen Start button eligibility wiring tests (T419)."""

from __future__ import annotations

import pygame

from game.research_eligibility import research_ui_eligibility
from game.research_state import ResearchState
from game.ui.research_screen import ResearchScreen
from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_tiles import draw_research_tiles
from tests.test_research_screen import _input_with_completed_laboratory


def _button_brightness(surface: pygame.Surface, rect: pygame.Rect) -> int:
    pixel = surface.get_at(rect.center)
    return sum(pixel[:3])


def test_research_screen_draw_uses_eligibility_for_start_buttons() -> None:
    surface = pygame.Surface((1280, 720))
    state = ResearchState()
    can_start, _ = research_ui_eligibility(
        research_state=state,
        registry=_input_with_completed_laboratory()[2],
    )
    assert can_start["1"] is True
    assert can_start["2"] is False
    ResearchScreen.draw(
        surface,
        research_state=state,
        research_can_start=can_start,
    )
    layout = ResearchScreen.layout(surface)
    tile1 = next(t for t in layout.content.tiles if t.research_id == "1")
    tile2 = next(t for t in layout.content.tiles if t.research_id == "2")
    assert _button_brightness(surface, tile1.start_button) > _button_brightness(
        surface, tile2.start_button
    )


def test_draw_research_tiles_reflects_eligibility_map() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    can_start = {"1": True, "2": False, "3": False, "4": False}
    draw_research_tiles(surface, content.tiles, research_can_start=can_start)
    tile1 = next(t for t in content.tiles if t.research_id == "1")
    tile2 = next(t for t in content.tiles if t.research_id == "2")
    assert _button_brightness(surface, tile1.start_button) > _button_brightness(
        surface, tile2.start_button
    )


def test_game_input_draw_panel_wires_eligibility() -> None:
    from game.ui.top_bar import TopBar

    inp, surface, registry = _input_with_completed_laboratory()
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
    surface.fill((28, 32, 40))
    inp.draw_panel(surface)
    screen_layout = ResearchScreen.layout(surface)
    tile1 = next(t for t in screen_layout.content.tiles if t.research_id == "1")
    tile2 = next(t for t in screen_layout.content.tiles if t.research_id == "2")
    assert _button_brightness(surface, tile1.start_button) > _button_brightness(
        surface, tile2.start_button
    )
    can_start, lock_reasons = research_ui_eligibility(
        research_state=ResearchState(),
        registry=registry,
    )
    assert can_start["1"] is True
    assert lock_reasons["2"] == "Requires Laboratory level 3"
