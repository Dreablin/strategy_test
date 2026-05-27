"""Full-screen Research menu shell."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pygame

from game.ui.research_screen_layout import (
    ResearchContentLayout,
    compute_content_layout,
)
from game.research_state import ResearchState
from game.ui.research_tile_tooltip import draw_research_tooltip_at_hover
from game.ui.research_tiles import draw_research_tiles

_PAD = 16
_CLOSE = 28
_TITLE = "Research"


@dataclass(frozen=True, slots=True)
class ResearchScreenLayout:
    overlay: pygame.Rect
    frame: pygame.Rect
    close: pygame.Rect
    content: ResearchContentLayout


class ResearchScreen:
    @staticmethod
    def layout(surface: pygame.Surface) -> ResearchScreenLayout:
        width, height = surface.get_size()
        overlay = pygame.Rect(0, 0, width, height)
        frame = pygame.Rect(0, 0, width, height)
        close = pygame.Rect(width - _PAD - _CLOSE, _PAD, _CLOSE, _CLOSE)
        return ResearchScreenLayout(
            overlay=overlay,
            frame=frame,
            close=close,
            content=compute_content_layout(surface),
        )

    @staticmethod
    def _draw_content(
        surface: pygame.Surface,
        content: ResearchContentLayout,
        *,
        research_state: ResearchState | None = None,
        hover_pos: tuple[int, int] | None = None,
        research_lock_reasons: Mapping[str, str] | None = None,
        research_can_start: Mapping[str, bool] | None = None,
    ) -> None:
        pygame.draw.rect(surface, (34, 38, 48), content.content, border_radius=8)
        pygame.draw.rect(surface, (48, 54, 66), content.technology_column, border_radius=6)
        label_font = pygame.font.Font(None, 20)
        tech_label = label_font.render("Technology", True, (190, 196, 208))
        surface.blit(
            tech_label,
            (
                content.technology_column.left + 10,
                content.technology_column.top + 8,
            ),
        )
        for row in content.tier_rows:
            pygame.draw.rect(surface, (40, 44, 54), row.row_rect)
            pygame.draw.rect(surface, (52, 58, 70), row.technology_slot, border_radius=4)
            pygame.draw.line(
                surface,
                (64, 70, 82),
                (row.row_rect.left, row.row_rect.bottom - 1),
                (row.row_rect.right, row.row_rect.bottom - 1),
                1,
            )
            tier_text = label_font.render(f"Tier {row.tier}", True, (150, 156, 168))
            surface.blit(
                tier_text,
                (
                    row.technology_slot.right + 12,
                    row.row_rect.top + 8,
                ),
            )
        draw_research_tiles(
            surface,
            content.tiles,
            research_state=research_state,
            research_can_start=research_can_start,
        )
        draw_research_tooltip_at_hover(
            surface,
            content.tiles,
            hover_pos,
            lock_reasons=research_lock_reasons,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        *,
        research_state: ResearchState | None = None,
        hover_pos: tuple[int, int] | None = None,
        research_lock_reasons: Mapping[str, str] | None = None,
        research_can_start: Mapping[str, bool] | None = None,
    ) -> ResearchScreenLayout:
        layout = ResearchScreen.layout(surface)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 200))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (28, 32, 40), layout.frame)
        pygame.draw.rect(surface, (56, 60, 68), layout.frame, width=2)

        title_font = pygame.font.Font(None, 36)
        title = title_font.render(_TITLE, True, (238, 240, 248))
        surface.blit(title, (layout.frame.left + _PAD, layout.frame.top + _PAD))

        ResearchScreen._draw_content(
            surface,
            layout.content,
            research_state=research_state,
            hover_pos=hover_pos,
            research_lock_reasons=research_lock_reasons,
            research_can_start=research_can_start,
        )

        pygame.draw.line(
            surface,
            (200, 82, 82),
            (layout.close.left + 6, layout.close.top + 6),
            (layout.close.right - 7, layout.close.bottom - 7),
            2,
        )
        pygame.draw.line(
            surface,
            (200, 82, 82),
            (layout.close.right - 7, layout.close.top + 6),
            (layout.close.left + 6, layout.close.bottom - 7),
            2,
        )
        return layout

    @staticmethod
    def click_action(surface: pygame.Surface, pos: tuple[int, int]) -> str | None:
        """Return ``\"close\"``, ``\"inside\"``, or ``None`` (outside overlay)."""
        layout = ResearchScreen.layout(surface)
        x, y = pos
        if layout.close.collidepoint(x, y):
            return "close"
        if layout.frame.collidepoint(x, y):
            return "inside"
        return None
