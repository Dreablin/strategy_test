"""Full-screen Research menu shell (content added in later tasks)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

_PAD = 16
_CLOSE = 28
_TITLE = "Research"


@dataclass(frozen=True, slots=True)
class ResearchScreenLayout:
    overlay: pygame.Rect
    frame: pygame.Rect
    close: pygame.Rect


class ResearchScreen:
    @staticmethod
    def layout(surface: pygame.Surface) -> ResearchScreenLayout:
        width, height = surface.get_size()
        overlay = pygame.Rect(0, 0, width, height)
        frame = pygame.Rect(0, 0, width, height)
        close = pygame.Rect(width - _PAD - _CLOSE, _PAD, _CLOSE, _CLOSE)
        return ResearchScreenLayout(overlay=overlay, frame=frame, close=close)

    @staticmethod
    def draw(surface: pygame.Surface) -> ResearchScreenLayout:
        layout = ResearchScreen.layout(surface)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 200))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (28, 32, 40), layout.frame)
        pygame.draw.rect(surface, (56, 60, 68), layout.frame, width=2)

        title_font = pygame.font.Font(None, 36)
        body_font = pygame.font.Font(None, 22)
        title = title_font.render(_TITLE, True, (238, 240, 248))
        surface.blit(title, (layout.frame.left + _PAD, layout.frame.top + _PAD))
        hint = body_font.render("Research tree — coming soon", True, (160, 166, 178))
        surface.blit(
            hint,
            (layout.frame.left + _PAD, layout.frame.top + _PAD + title.get_height() + 8),
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
