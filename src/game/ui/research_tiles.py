"""Draw research tiles (image + title) on the research screen."""

from __future__ import annotations

import pygame

from game.research_assets import research_image_for_id
from game.research_config import RESEARCH_BY_ID
from game.research_state import ResearchState
from game.ui.research_tile_layout import ResearchTileLayout
from game.ui.research_tile_visual import research_tile_image_alpha, research_tile_title_color


def draw_research_tiles(
    surface: pygame.Surface,
    tiles: tuple[ResearchTileLayout, ...],
    *,
    research_state: ResearchState | None = None,
) -> None:
    title_font = pygame.font.Font(None, 18)
    for tile in tiles:
        entry = RESEARCH_BY_ID[tile.research_id]
        image = research_image_for_id(entry.id, size=tile.image_rect.width)
        alpha = research_tile_image_alpha(tile.research_id, research_state)
        if alpha < 255:
            image = image.copy()
            image.set_alpha(alpha)
        surface.blit(image, tile.image_rect.topleft)
        title_color = research_tile_title_color(tile.research_id, research_state)
        label = title_font.render(entry.name, True, title_color)
        if alpha < 255:
            label = label.copy()
            label.set_alpha(alpha)
        label_x = tile.title_rect.left + max(0, (tile.title_rect.width - label.get_width()) // 2)
        surface.blit(label, (label_x, tile.title_rect.top))
