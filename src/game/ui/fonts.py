"""Cached UI font loading with Cyrillic-capable bundled TTF."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

_FONT_PATH = Path(__file__).resolve().parents[3] / "assets" / "fonts" / "DejaVuSans.ttf"
_TTF_SIZE_SCALE = 0.82


def _scaled_ttf_size(size: int) -> int:
    return max(8, int(round(int(size) * _TTF_SIZE_SCALE)))


@lru_cache(maxsize=32)
def ui_font(size: int) -> pygame.font.Font:
    if _FONT_PATH.is_file():
        return pygame.font.Font(str(_FONT_PATH), _scaled_ttf_size(size))
    return pygame.font.Font(None, size)


def render_fitted_ui_text(
    text: str,
    max_width: int,
    *,
    sizes: tuple[int, ...] = (28, 24, 22, 20, 18, 16),
    color: tuple[int, int, int] = (238, 240, 248),
) -> pygame.Surface:
    """Render UI text, stepping down font size until it fits ``max_width``."""
    for size in sizes:
        surf = ui_font(size).render(text, True, color)
        if surf.get_width() <= max_width:
            return surf
    return surf
