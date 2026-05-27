"""Draw research tiles (image + title) on the research screen."""

from __future__ import annotations

from collections.abc import Mapping

import pygame

from game.research_assets import research_image_for_id
from game.research_config import RESEARCH_BY_ID
from game.research_state import ResearchState
from game.ui.research_start_button import draw_research_start_button
from game.ui.research_tile_layout import ResearchTileLayout
from game.ui.research_tile_visual import research_tile_image_alpha, research_tile_title_color


def draw_research_tiles(
    surface: pygame.Surface,
    tiles: tuple[ResearchTileLayout, ...],
    *,
    research_state: ResearchState | None = None,
    research_can_start: Mapping[str, bool] | None = None,
) -> None:
    eligibility = research_can_start if research_can_start is not None else {}
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
        can_start = bool(eligibility.get(tile.research_id, False))
        draw_research_start_button(surface, tile.start_button, enabled=can_start)
