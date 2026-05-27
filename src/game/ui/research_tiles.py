"""Draw research tiles (image + title) on the research screen."""

from __future__ import annotations

import pygame

from game.research_assets import research_image_for_id
from game.research_config import RESEARCH_BY_ID
from game.ui.research_tile_layout import ResearchTileLayout


def draw_research_tiles(
    surface: pygame.Surface,
    tiles: tuple[ResearchTileLayout, ...],
) -> None:
    title_font = pygame.font.Font(None, 18)
    for tile in tiles:
        entry = RESEARCH_BY_ID[tile.research_id]
        image = research_image_for_id(entry.id, size=tile.image_rect.width)
        surface.blit(image, tile.image_rect.topleft)
        label = title_font.render(entry.name, True, (232, 236, 244))
        label_x = tile.title_rect.left + max(0, (tile.title_rect.width - label.get_width()) // 2)
        surface.blit(label, (label_x, tile.title_rect.top))
