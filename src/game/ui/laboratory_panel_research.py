"""Active research image and dynamic input rows for the Laboratory panel."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.research_assets import research_image_for_id
from game.research_state import ResearchState
from game.resource_catalog import resource_display_label

_IMAGE_SIZE = 48
_LINE_H = 20
SECTION_PAD = 8


def research_storage_section_height(laboratory: Laboratory) -> int:
    if not laboratory.has_research_input_storage():
        return 0
    resources = laboratory.research_input_resources()
    if not resources:
        return 0
    return SECTION_PAD + _IMAGE_SIZE + 8 + len(resources) * _LINE_H + 12


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
    """Draw active research image and per-resource delivered/capacity rows."""
    if research_state is None or research_state.active_research_id() is None:
        return
    if not laboratory.has_research_input_storage():
        return
    active_id = research_state.active_research_id()
    assert active_id is not None
    left = frame.left + SECTION_PAD
    y = section_top
    image = research_image_for_id(active_id, size=_IMAGE_SIZE)
    image_rect = pygame.Rect(left, y, _IMAGE_SIZE, _IMAGE_SIZE)
    surface.blit(image, image_rect.topleft)
    title_font = pygame.font.Font(None, 20)
    title = title_font.render("Active research", True, (190, 196, 208))
    surface.blit(title, (image_rect.right + 10, y + 4))
    body = pygame.font.Font(None, 20)
    line_y = image_rect.bottom + 8
    for resource in sorted(laboratory.research_input_resources()):
        text = body.render(research_input_line(laboratory, resource), True, (200, 204, 214))
        surface.blit(text, (left, line_y))
        line_y += _LINE_H
