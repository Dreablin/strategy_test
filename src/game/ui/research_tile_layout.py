"""Per-research tile placement from configured tier and column."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.research_config import RESEARCH_DEFINITIONS, ResearchDefinition
from game.ui.research_screen_layout import ResearchContentLayout, ResearchTierRowLayout

_TILE_PAD = 6
_IMAGE_SIZE = 52
_TITLE_LINE_H = 18


@dataclass(frozen=True, slots=True)
class ResearchTileLayout:
    research_id: str
    tier: int
    column: int
    tile_rect: pygame.Rect
    image_rect: pygame.Rect
    title_rect: pygame.Rect


def max_configured_column() -> int:
    if not RESEARCH_DEFINITIONS:
        return 0
    return max(entry.column for entry in RESEARCH_DEFINITIONS)


def _tier_row(content: ResearchContentLayout, tier: int) -> ResearchTierRowLayout:
    for row in content.tier_rows:
        if row.tier == tier:
            return row
    raise KeyError(f"unknown tier row {tier}")


def column_slot_rect(
    row: ResearchTierRowLayout,
    column: int,
    *,
    max_column: int,
) -> pygame.Rect:
    """Slot rectangle for a research at ``column`` within ``row``."""
    pad = _TILE_PAD
    if column == 0:
        return row.technology_slot.inflate(-pad, -pad)
    area_left = row.technology_slot.right + pad
    area_width = row.row_rect.right - area_left - pad
    area = pygame.Rect(area_left, row.row_rect.top + pad, max(1, area_width), row.row_rect.height - pad * 2)
    if column <= 0 or max_column <= 0:
        return area
    slot_w = max(1, area.width // max_column)
    x = area.left + (column - 1) * slot_w
    return pygame.Rect(x, area.top, max(1, slot_w - pad), area.height)


def layout_tile_for_entry(
    entry: ResearchDefinition,
    content: ResearchContentLayout,
    *,
    max_column: int | None = None,
) -> ResearchTileLayout:
    max_col = max_configured_column() if max_column is None else max_column
    row = _tier_row(content, entry.tier)
    slot = column_slot_rect(row, entry.column, max_column=max_col)
    img_size = min(_IMAGE_SIZE, slot.width - 4, max(16, slot.height - _TITLE_LINE_H - 8))
    image_rect = pygame.Rect(
        slot.left + (slot.width - img_size) // 2,
        slot.top + 4,
        img_size,
        img_size,
    )
    title_rect = pygame.Rect(slot.left, image_rect.bottom + 2, slot.width, _TITLE_LINE_H)
    return ResearchTileLayout(
        research_id=entry.id,
        tier=entry.tier,
        column=entry.column,
        tile_rect=slot,
        image_rect=image_rect,
        title_rect=title_rect,
    )


def compute_research_tile_layouts(content: ResearchContentLayout) -> tuple[ResearchTileLayout, ...]:
    max_col = max_configured_column()
    return tuple(
        layout_tile_for_entry(entry, content, max_column=max_col) for entry in RESEARCH_DEFINITIONS
    )
