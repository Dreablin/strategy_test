"""Research screen tier rows and Technology column layout."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.research_config import RESEARCH_DEFINITIONS

_TIER_COUNT = 4
_SCREEN_PAD = 16
_HEADER_BOTTOM = 72
_TECHNOLOGY_COLUMN_WIDTH = 140


@dataclass(frozen=True, slots=True)
class ResearchTierRowLayout:
    """One configured tier row (``tier`` 1..4) with a column-0 Technology slot."""

    tier: int
    row_rect: pygame.Rect
    technology_slot: pygame.Rect


@dataclass(frozen=True, slots=True)
class ResearchContentLayout:
    content: pygame.Rect
    technology_column: pygame.Rect
    tier_rows: tuple[ResearchTierRowLayout, ...]


def configured_tier_count() -> int:
    return _TIER_COUNT


def technology_column_width() -> int:
    return _TECHNOLOGY_COLUMN_WIDTH


def compute_content_layout(surface: pygame.Surface) -> ResearchContentLayout:
    """Lay out four equal-height tier rows and the left Technology column."""
    width, height = surface.get_size()
    content = pygame.Rect(
        _SCREEN_PAD,
        _HEADER_BOTTOM,
        width - _SCREEN_PAD * 2,
        height - _HEADER_BOTTOM - _SCREEN_PAD,
    )
    technology_column = pygame.Rect(
        content.left,
        content.top,
        _TECHNOLOGY_COLUMN_WIDTH,
        content.height,
    )
    base_row_h, remainder = divmod(max(1, content.height), _TIER_COUNT)
    tier_rows: list[ResearchTierRowLayout] = []
    y = content.top
    for tier in range(1, _TIER_COUNT + 1):
        row_h = base_row_h + (1 if tier <= remainder else 0)
        row_rect = pygame.Rect(content.left, y, content.width, row_h)
        technology_slot = pygame.Rect(content.left, y, _TECHNOLOGY_COLUMN_WIDTH, row_h)
        tier_rows.append(
            ResearchTierRowLayout(
                tier=tier,
                row_rect=row_rect,
                technology_slot=technology_slot,
            )
        )
        y += row_h
    return ResearchContentLayout(
        content=content,
        technology_column=technology_column,
        tier_rows=tuple(tier_rows),
    )


def technology_entries_by_tier() -> dict[int, tuple[str, ...]]:
    """Map tier row number to research ids configured in column 0."""
    by_tier: dict[int, list[str]] = {tier: [] for tier in range(1, _TIER_COUNT + 1)}
    for entry in RESEARCH_DEFINITIONS:
        if entry.column == 0 and _TIER_COUNT >= entry.tier >= 1:
            by_tier[entry.tier].append(entry.id)
    return {tier: tuple(ids) for tier, ids in by_tier.items()}
