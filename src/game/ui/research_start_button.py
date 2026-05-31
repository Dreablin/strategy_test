"""Per-tile Start button rendering for the research screen."""

from __future__ import annotations

import pygame
from game.ui.fonts import ui_font

_START_LABEL = "Start"
_ENABLED_BG = (64, 110, 168)
_ENABLED_BORDER = (96, 140, 200)
_ENABLED_FG = (240, 242, 250)
_DISABLED_BG = (48, 52, 60)
_DISABLED_BORDER = (68, 72, 80)
_DISABLED_FG = (120, 124, 132)


def draw_research_start_button(
    surface: pygame.Surface,
    button: pygame.Rect,
    *,
    enabled: bool,
) -> None:
    bg = _ENABLED_BG if enabled else _DISABLED_BG
    border = _ENABLED_BORDER if enabled else _DISABLED_BORDER
    fg = _ENABLED_FG if enabled else _DISABLED_FG
    pygame.draw.rect(surface, bg, button, border_radius=5)
    pygame.draw.rect(surface, border, button, width=1, border_radius=5)
    font = ui_font(20)
    label = font.render(_START_LABEL, True, fg)
    if not enabled:
        label = label.copy()
        label.set_alpha(160)
    surface.blit(
        label,
        (
            button.centerx - label.get_width() // 2,
            button.centery - label.get_height() // 2,
        ),
    )
