"""Research tile rendering tests (T411)."""

from __future__ import annotations

import pygame

from game.research_config import RESEARCH_BY_ID, RESEARCH_DEFINITIONS
from game.research_technology_chain import TECHNOLOGY_IDS
from game.ui.research_screen import ResearchScreen
from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_tile_layout import layout_tile_for_entry


def test_one_tile_layout_per_configured_research() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    assert len(content.tiles) == len(RESEARCH_DEFINITIONS)
    assert {tile.research_id for tile in content.tiles} == {entry.id for entry in RESEARCH_DEFINITIONS}


def test_technology_tiles_use_column_zero_slots() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    tier_rows = {row.tier: row for row in content.tier_rows}
    for entry in RESEARCH_DEFINITIONS:
        if entry.id not in TECHNOLOGY_IDS:
            continue
        tile = next(t for t in content.tiles if t.research_id == entry.id)
        assert tile.tier == entry.tier
        assert tile.column == entry.column
        slot = tier_rows[entry.tier].technology_slot
        assert slot.contains(tile.tile_rect)
        assert slot.contains(tile.image_rect)


def test_column_one_places_right_of_technology_column() -> None:
    from dataclasses import replace

    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    entry = RESEARCH_DEFINITIONS[0]
    fake = replace(entry, column=1)
    tile = layout_tile_for_entry(fake, content, max_column=2)
    row = next(r for r in content.tier_rows if r.tier == fake.tier)
    assert tile.image_rect.left >= row.technology_slot.right


def test_tile_image_rect_fits_inside_row() -> None:
    surface = pygame.Surface((1024, 768))
    content = compute_content_layout(surface)
    for tile in content.tiles:
        row = next(r for r in content.tier_rows if r.tier == tile.tier)
        assert row.row_rect.contains(tile.image_rect)
        assert tile.image_rect.width > 0
        assert tile.title_rect.top >= tile.image_rect.bottom


def test_draw_research_tiles_pixels_differ_from_row_background() -> None:
    surface = pygame.Surface((1280, 720))
    layout = ResearchScreen.draw(surface)
    tile = next(t for t in layout.content.tiles if t.research_id == "1")
    image_pixel = surface.get_at(tile.image_rect.center)
    row = next(r for r in layout.content.tier_rows if r.tier == 1)
    row_pixel = surface.get_at(
        (row.technology_slot.right + 80, row.row_rect.centery),
    )
    assert image_pixel[:3] != row_pixel[:3]


def test_draw_renders_title_text_pixels() -> None:
    surface = pygame.Surface((1280, 720))
    layout = ResearchScreen.draw(surface)
    tile = next(t for t in layout.content.tiles if t.research_id == "2")
    entry = RESEARCH_BY_ID["2"]
    row = next(r for r in layout.content.tier_rows if r.tier == tile.tier)
    row_bg = surface.get_at((row.technology_slot.right + 60, row.row_rect.centery))
    title_pixel = surface.get_at((tile.title_rect.centerx, tile.title_rect.centery))
    assert title_pixel[:3] != row_bg[:3]
    assert entry.name.startswith("Technology")
