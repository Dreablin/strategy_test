"""Research tile hover tooltip tests (T414)."""

from __future__ import annotations

import pygame

from game import i18n
from game.lock_reasons import lock_reason_no_laboratory
from game.ui.research_screen import ResearchScreen
from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_tile_tooltip import (
    draw_research_tile_tooltip,
    draw_research_tooltip_at_hover,
    format_research_tooltip_lines,
    hovered_research_tile,
    research_tooltip_info_for_id,
)


def test_hovered_research_tile_hit_tests_tile_rect() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    tile = content.tiles[0]
    assert hovered_research_tile(content.tiles, tile.tile_rect.center) is tile
    assert hovered_research_tile(content.tiles, (0, 0)) is None


def test_format_tooltip_includes_cost_points_and_dependencies() -> None:
    info = research_tooltip_info_for_id("2")
    lines = format_research_tooltip_lines(info)
    assert i18n.t("ui.research.cost_line", items=i18n.t("resource.boards") + " 15") in lines or any(
        i18n.t("resource.boards") in line for line in lines
    )
    assert i18n.t("ui.research.points_line", points=10000) in lines
    assert i18n.t("research.1.name") in " ".join(lines)
    assert i18n.t("ui.research.effect_line", effect=i18n.t("research.2.effect")) in lines


def test_format_tooltip_shows_lock_reason_when_supplied() -> None:
    reason = "Active research in progress"
    info = research_tooltip_info_for_id("1", lock_reason=reason)
    lines = format_research_tooltip_lines(info)
    assert i18n.t("ui.research.locked_line", reason=reason) in lines


def test_draw_tooltip_renders_visible_panel() -> None:
    surface = pygame.Surface((400, 200))
    surface.fill((28, 32, 40))
    info = research_tooltip_info_for_id("1", lock_reason="Need Laboratory")
    anchor = pygame.Rect(10, 20, 80, 120)
    box = draw_research_tile_tooltip(surface, anchor, info)
    assert box.width > 40 and box.height > 30
    center = surface.get_at(box.center)
    assert sum(center[:3]) > 30


def test_hover_draws_tooltip_on_research_screen() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    tile = content.tiles[0]
    ResearchScreen.draw(
        surface,
        hover_pos=tile.tile_rect.center,
        research_lock_reasons={"1": lock_reason_no_laboratory()},
    )
    tooltip_rect = draw_research_tooltip_at_hover(
        surface,
        content.tiles,
        tile.tile_rect.center,
        lock_reasons={"1": lock_reason_no_laboratory()},
    )
    assert tooltip_rect is not None
    px = surface.get_at(tooltip_rect.center)
    assert sum(px[:3]) > 40


def test_no_tooltip_when_hover_outside_tiles() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    assert draw_research_tooltip_at_hover(surface, content.tiles, (2, 2)) is None
