"""Research tile images: disk-first with procedural fallback."""

from __future__ import annotations

import functools
import re
from pathlib import Path

import pygame

from game.assets import _load_png
from game.research_config import RESEARCH_BY_ID

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RESEARCH_ROOT = _PROJECT_ROOT / "assets" / "research"

_TIER_COLORS: dict[int, tuple[int, int, int]] = {
    1: (70, 110, 180),
    2: (90, 140, 200),
    3: (110, 170, 220),
    4: (130, 200, 240),
}


def _tier_from_image_key(image_key: str) -> int:
    match = re.fullmatch(r"technology_(\d+)", image_key)
    if match:
        return max(1, min(4, int(match.group(1))))
    return (abs(hash(image_key)) % 4) + 1


def _procedural_research_image(image_key: str, size: int) -> pygame.Surface:
    sz = max(1, int(size))
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    color = _TIER_COLORS.get(_tier_from_image_key(image_key), (100, 140, 200))
    rect = pygame.Rect(2, 2, sz - 4, sz - 4)
    pygame.draw.rect(surf, color, rect, border_radius=max(2, sz // 8))
    pygame.draw.rect(surf, (24, 30, 42), rect, width=max(1, sz // 16), border_radius=max(2, sz // 8))
    cx, cy = sz // 2, sz // 2
    pygame.draw.circle(surf, (220, 232, 248), (cx, cy), max(3, sz // 6), 2)
    return surf


@functools.lru_cache(maxsize=32)
def research_image(image_key: str, size: int = 64) -> pygame.Surface:
    """Load a research tile image by configured ``image_key``."""
    key = str(image_key).strip()
    if not key:
        raise ValueError("image_key must be non-empty")
    sz = max(1, int(size))
    path = _RESEARCH_ROOT / f"{key}.png"
    loaded = _load_png(str(path))
    base = loaded if loaded is not None else _procedural_research_image(key, sz)
    if base.get_width() == sz and base.get_height() == sz:
        return base
    return pygame.transform.smoothscale(base, (sz, sz))


def research_image_for_id(research_id: str, size: int = 64) -> pygame.Surface:
    """Load the research tile image for a configured research id."""
    definition = RESEARCH_BY_ID[str(research_id)]
    return research_image(definition.image_key, size=size)


def clear_research_asset_caches() -> None:
    research_image.cache_clear()
