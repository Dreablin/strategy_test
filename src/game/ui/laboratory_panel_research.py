"""Active research image, progress, and dynamic input rows for the Laboratory panel."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.research_assets import research_image_for_id
from game.research_config import RESEARCH_BY_ID
from game.research_state import ResearchState
from game.resource_catalog import resource_display_label

_IMAGE_SIZE = 48
_LINE_H = 20
_PROGRESS_BAR_H = 12
_POINTS_LINE_H = 20
_SECTION_GAP = 8
SECTION_PAD = 8


def research_points_display(research_state: ResearchState) -> tuple[int, int]:
    """Return ``(accumulated, required)`` for the active research."""
    active_id = research_state.active_research_id()
    if active_id is None:
        return 0, 0
    required = RESEARCH_BY_ID[active_id].required_points
    return research_state.accumulated_points(), required


def research_points_label(research_state: ResearchState) -> str:
    current, required = research_points_display(research_state)
    return f"{current} / {required}"


def research_points_fill_ratio(research_state: ResearchState) -> float:
    current, required = research_points_display(research_state)
    if required <= 0:
        return 0.0
    return min(1.0, current / required)


def _progress_block_height(*, research_state: ResearchState | None) -> int:
    if research_state is None or research_state.active_research_id() is None:
        return 0
    return _PROGRESS_BAR_H + _SECTION_GAP + _POINTS_LINE_H + _SECTION_GAP


def research_storage_section_height(
    laboratory: Laboratory,
    *,
    research_state: ResearchState | None = None,
) -> int:
    if not laboratory.has_research_input_storage():
        return 0
    resources = laboratory.research_input_resources()
    if not resources:
        return 0
    return (
        SECTION_PAD
        + _IMAGE_SIZE
        + _SECTION_GAP
        + _progress_block_height(research_state=research_state)
        + len(resources) * _LINE_H
        + 12
    )


def research_input_line(laboratory: Laboratory, resource: str) -> str:
    amount = laboratory.research_input_amount(resource)
    capacity = laboratory.research_input_capacity(resource)
    return f"{resource_display_label(resource)}: {amount} / {capacity}"


def draw_research_storage_section(
    surface: pygame.Surface,
    frame: pygame.Rect,
    laboratory: Laboratory,
    *,
    research_state: ResearchState | None,
    section_top: int,
) -> None:
    """Draw active research image, point progress, and per-resource rows."""
    if research_state is None or research_state.active_research_id() is None:
        return
    if not laboratory.has_research_input_storage():
        return
    active_id = research_state.active_research_id()
    assert active_id is not None
    left = frame.left + SECTION_PAD
    content_width = frame.width - 2 * SECTION_PAD
    y = section_top
    image = research_image_for_id(active_id, size=_IMAGE_SIZE)
    image_rect = pygame.Rect(left, y, _IMAGE_SIZE, _IMAGE_SIZE)
    surface.blit(image, image_rect.topleft)
    title_font = pygame.font.Font(None, 20)
    title = title_font.render("Active research", True, (190, 196, 208))
    surface.blit(title, (image_rect.right + 10, y + 4))
    body = pygame.font.Font(None, 20)
    line_y = image_rect.bottom + _SECTION_GAP
    bar_rect = pygame.Rect(left, line_y, content_width, _PROGRESS_BAR_H)
    pygame.draw.rect(surface, (52, 58, 66), bar_rect, border_radius=4)
    fill_ratio = research_points_fill_ratio(research_state)
    if fill_ratio > 0:
        fill_w = max(1, int(bar_rect.width * fill_ratio))
        fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_w, bar_rect.height)
        pygame.draw.rect(surface, (92, 148, 210), fill_rect, border_radius=4)
    pygame.draw.rect(surface, (116, 124, 136), bar_rect, width=1, border_radius=4)
    line_y = bar_rect.bottom + _SECTION_GAP
    points_text = body.render(research_points_label(research_state), True, (200, 204, 214))
    surface.blit(points_text, (left, line_y))
    line_y += _POINTS_LINE_H + _SECTION_GAP
    for resource in sorted(laboratory.research_input_resources()):
        text = body.render(research_input_line(laboratory, resource), True, (200, 204, 214))
        surface.blit(text, (left, line_y))
        line_y += _LINE_H
