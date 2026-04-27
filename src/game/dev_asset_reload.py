"""Temporary dev tool: top-bar button to force asset cache reload.

All logic for this feature is intentionally centralized here so it can be
removed later with minimal cleanup.
"""

from __future__ import annotations

import pygame

ASSET_RELOAD_REQUEST = pygame.USEREVENT + 70
ENABLED = True

_BTN_W = 110
_BTN_H = 30
_MARGIN = 8
_LABEL = "Reload"
_FLASH_MS = 1200
_last_reload_ms = -10_000


def button_rect(surface: pygame.Surface) -> pygame.Rect:
    """Button rectangle in the top HUD area."""
    w = surface.get_width()
    return pygame.Rect(w - _BTN_W - _MARGIN, _MARGIN, _BTN_W, _BTN_H)


def handle_click(surface: pygame.Surface, pos: tuple[int, int]) -> bool:
    """Post reload request event if click hits the dev button."""
    if not ENABLED:
        return False
    if button_rect(surface).collidepoint(pos):
        pygame.event.post(pygame.event.Event(ASSET_RELOAD_REQUEST))
        return True
    return False


def process_event(event: pygame.event.Event) -> bool:
    """Handle posted reload request event; return True if consumed."""
    if not ENABLED or event.type != ASSET_RELOAD_REQUEST:
        return False
    perform_reload()
    return True


def perform_reload() -> None:
    """Force-clear all asset caches so changed files/metadata are reloaded."""
    global _last_reload_ms
    from game.assets import clear_asset_caches

    clear_asset_caches()
    _last_reload_ms = pygame.time.get_ticks()


def draw_button(surface: pygame.Surface) -> None:
    """Draw reload button (and short success flash) on top HUD."""
    if not ENABLED:
        return
    rect = button_rect(surface)
    now = pygame.time.get_ticks()
    flashed = now - _last_reload_ms <= _FLASH_MS
    bg = (46, 76, 48) if flashed else (54, 58, 68)
    border = (114, 196, 118) if flashed else (94, 98, 108)
    fg = (228, 248, 230) if flashed else (232, 234, 240)

    pygame.draw.rect(surface, bg, rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=6)

    font = pygame.font.Font(None, 22)
    label = "Updated" if flashed else _LABEL
    text = font.render(label, True, fg)
    surface.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
