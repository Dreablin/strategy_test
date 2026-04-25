"""Procedural pygame surfaces for tiles, buildings, workers, and HUD icons."""

import functools

import pygame

from game.config import TILE_H, TILE_W


def _diamond_points(w: int, h: int) -> list[tuple[int, int]]:
    return [(w // 2, 0), (w - 1, h // 2), (w // 2, h - 1), (0, h // 2)]


@functools.lru_cache(maxsize=1)
def grass_tile() -> pygame.Surface:
    surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
    pts = _diamond_points(TILE_W, TILE_H)
    pygame.draw.polygon(surf, (72, 152, 84), pts)
    pygame.draw.polygon(surf, (36, 92, 44), pts, 1)
    return surf


@functools.lru_cache(maxsize=1)
def tree_tile() -> pygame.Surface:
    surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
    pts = _diamond_points(TILE_W, TILE_H)
    pygame.draw.polygon(surf, (34, 58, 34), pts)
    cx, top = TILE_W // 2, TILE_H // 4
    pygame.draw.circle(surf, (28, 110, 48), (cx, top + 4), TILE_H // 3)
    pygame.draw.rect(surf, (86, 52, 28), (cx - 4, top + 8, 8, TILE_H // 2))
    return surf


def _building_palette(b_type: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    t = b_type.lower().replace(" ", "_")
    palettes: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
        "town_hall": ((180, 160, 120), (90, 70, 50)),
        "lumber_camp": ((120, 90, 60), (60, 45, 30)),
        "stone_mine": ((140, 140, 150), (70, 70, 80)),
        "iron_mine": ((150, 110, 100), (80, 55, 50)),
        "farm": ((170, 150, 90), (90, 120, 60)),
    }
    return palettes.get(t, ((120, 120, 130), (60, 60, 70)))


@functools.lru_cache(maxsize=128)
def building_sprite(b_type: str, level: int) -> pygame.Surface:
    w, h = TILE_W + 8, TILE_H + 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    fill, outline = _building_palette(b_type)
    body = pygame.Rect(6, 8, w - 12, h - 14)
    pygame.draw.rect(surf, fill, body, border_radius=4)
    pygame.draw.rect(surf, outline, body, 2, border_radius=4)
    lvl = max(1, min(level, 10))
    pygame.draw.rect(
        surf,
        (220, 200, 80),
        (body.centerx - 6, body.top - 6, 12, 8),
        border_radius=2,
    )
    font = pygame.font.Font(None, 12)
    txt = font.render(str(lvl), True, (20, 20, 20))
    surf.blit(txt, (body.right - txt.get_width() - 4, body.top + 2))
    return surf


def _worker_color(w_type: str) -> tuple[int, int, int]:
    t = w_type.upper().replace(" ", "_")
    colors: dict[str, tuple[int, int, int]] = {
        "LUMBERJACK": (40, 140, 220),
        "STONECUTTER": (160, 160, 170),
        "MINER": (200, 90, 70),
        "FARMER": (230, 200, 60),
    }
    return colors.get(t, (200, 200, 220))


@functools.lru_cache(maxsize=32)
def worker_dot(w_type: str) -> pygame.Surface:
    size = 14
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, _worker_color(w_type), (size // 2, size // 2), size // 2 - 1)
    pygame.draw.circle(surf, (20, 20, 30), (size // 2, size // 2), size // 2 - 1, 1)
    return surf


def _resource_colors(name: str) -> tuple[int, int, int]:
    colors: dict[str, tuple[int, int, int]] = {
        "food": (230, 170, 80),
        "wood": (150, 100, 60),
        "stone": (170, 170, 180),
        "iron": (190, 120, 110),
    }
    return colors.get(name.lower(), (160, 160, 200))


@functools.lru_cache(maxsize=16)
def resource_icon(name: str) -> pygame.Surface:
    size = 28
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = _resource_colors(name)
    pygame.draw.circle(surf, c, (size // 2, size // 2), size // 2 - 2)
    pygame.draw.circle(surf, (30, 30, 40), (size // 2, size // 2), size // 2 - 2, 2)
    return surf
