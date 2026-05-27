"""Research screen four-row layout tests (T410)."""

from __future__ import annotations

import pygame

from game.research_config import RESEARCH_DEFINITIONS
from game.ui.research_screen import ResearchScreen
from game.ui.research_screen_layout import (
    compute_content_layout,
    configured_tier_count,
    technology_column_width,
    technology_entries_by_tier,
)


def test_configured_technology_entries_one_per_tier_column_zero() -> None:
    by_tier = technology_entries_by_tier()
    assert len(by_tier) == configured_tier_count()
    for tier in range(1, configured_tier_count() + 1):
        ids = by_tier[tier]
        assert len(ids) == 1
        entry = next(e for e in RESEARCH_DEFINITIONS if e.id == ids[0])
        assert entry.tier == tier
        assert entry.column == 0


def test_content_layout_has_four_equal_height_tier_rows() -> None:
    surface = pygame.Surface((1280, 720))
    layout = compute_content_layout(surface)
    assert len(layout.tier_rows) == 4
    heights = [row.row_rect.height for row in layout.tier_rows]
    assert max(heights) - min(heights) <= 1
    assert sum(heights) == layout.content.height
    assert layout.tier_rows[0].tier == 1
    assert layout.tier_rows[-1].tier == 4


def test_technology_column_is_left_static_strip() -> None:
    surface = pygame.Surface((900, 600))
    layout = compute_content_layout(surface)
    assert layout.technology_column.left == layout.content.left
    assert layout.technology_column.width == technology_column_width()
    assert layout.technology_column.height == layout.content.height
    for row in layout.tier_rows:
        assert row.technology_slot.left == layout.technology_column.left
        assert row.technology_slot.width == layout.technology_column.width
        assert row.technology_slot.centery == row.row_rect.centery


def test_tier_rows_stack_within_content_without_gaps() -> None:
    surface = pygame.Surface((1024, 768))
    layout = compute_content_layout(surface)
    assert layout.tier_rows[0].row_rect.top == layout.content.top
    assert layout.tier_rows[-1].row_rect.bottom == layout.content.bottom
    for upper, lower in zip(layout.tier_rows, layout.tier_rows[1:], strict=False):
        assert upper.row_rect.bottom == lower.row_rect.top


def test_research_screen_layout_includes_content_regions() -> None:
    surface = pygame.Surface((800, 600))
    layout = ResearchScreen.layout(surface)
    assert len(layout.content.tier_rows) == 4
    assert layout.content.technology_column.width > 0


def test_draw_marks_technology_column_and_row_bands() -> None:
    surface = pygame.Surface((1280, 720))
    screen_layout = ResearchScreen.draw(surface)
    tech_center = screen_layout.content.technology_column.center
    row_center = screen_layout.content.tier_rows[1].row_rect.center
    tech_pixel = surface.get_at(tech_center)
    row_pixel = surface.get_at(row_center)
    assert tech_pixel != row_pixel
