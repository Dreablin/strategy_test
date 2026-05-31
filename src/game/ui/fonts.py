"""Cached UI font loading with Cyrillic-capable bundled TTF."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

_FONT_PATH = Path(__file__).resolve().parents[3] / "assets" / "fonts" / "DejaVuSans.ttf"


@lru_cache(maxsize=32)
def ui_font(size: int) -> pygame.font.Font:
    if _FONT_PATH.is_file():
        return pygame.font.Font(str(_FONT_PATH), size)
    return pygame.font.Font(None, size)
