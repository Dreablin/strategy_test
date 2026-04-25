"""Fixed-height bottom strip for choosing a building to place."""

from __future__ import annotations

import pygame

from game.assets import building_sprite, resource_icon
from game.config import BUILD_COST_WOOD
from game.resources import ResourceManager

_BAR_HEIGHT = 96
# Distinct from other user events; carries `building_type: str` (e.g. `"LUMBER_CAMP"`).
BUILD_MENU_SELECT = pygame.USEREVENT + 10

_BUTTONS: tuple[tuple[str, str, str], ...] = (
    ("lumber_camp", "Lumber", "LUMBER_CAMP"),
    ("stone_mine", "Stone", "STONE_MINE"),
    ("iron_mine", "Iron", "IRON_MINE"),
    ("farm", "Farm", "FARM"),
)


def _button_rects(surface: pygame.Surface) -> list[tuple[pygame.Rect, str, str]]:
    w, h = surface.get_width(), surface.get_height()
    y0 = h - _BAR_HEIGHT
    col_w = max(1, w // len(_BUTTONS))
    out: list[tuple[pygame.Rect, str, str]] = []
    for i, (asset_key, _label, tag) in enumerate(_BUTTONS):
        out.append((pygame.Rect(i * col_w, y0, col_w, _BAR_HEIGHT), asset_key, tag))
    return out


class BottomBar:
    """Four build slots; posts `BUILD_MENU_SELECT` with `building_type` when an affordable slot is clicked."""

    @staticmethod
    def draw(surface: pygame.Surface, resources: ResourceManager) -> None:
        w, h = surface.get_width(), surface.get_height()
        y0 = h - _BAR_HEIGHT
        pygame.draw.rect(surface, (26, 28, 34), (0, y0, w, _BAR_HEIGHT))
        pygame.draw.line(surface, (48, 52, 60), (0, y0), (w, y0))

        can_afford = resources.get("wood") >= BUILD_COST_WOOD
        font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 18)

        for rect, asset_key, _tag in _button_rects(surface):
            pygame.draw.rect(surface, (36, 40, 48), rect.inflate(-6, -10), border_radius=6)

            inner = rect.inflate(-12, -14)
            spr = pygame.transform.smoothscale(
                building_sprite(asset_key, 1),
                (min(56, inner.width // 3), min(48, inner.height - 28)),
            )
            sx = inner.left + 8
            sy = inner.centery - spr.get_height() // 2
            surface.blit(spr, (sx, sy))

            label = next(name for key, name, _ in _BUTTONS if key == asset_key)
            fg = (220, 222, 230) if can_afford else (110, 112, 120)
            name_s = font.render(label, True, fg)
            tx = sx + spr.get_width() + 8
            ty_name = inner.top + 8
            surface.blit(name_s, (tx, ty_name))

            cost_y = ty_name + name_s.get_height() + 4
            cost_s = small_font.render("100", True, fg)
            wood_ic = pygame.transform.smoothscale(resource_icon("wood"), (20, 20))
            surface.blit(cost_s, (tx, cost_y))
            surface.blit(wood_ic, (tx + cost_s.get_width() + 4, cost_y - 1))

            if not can_afford:
                shade = pygame.Surface(rect.size, pygame.SRCALPHA)
                shade.fill((20, 22, 28, 140))
                surface.blit(shade, rect.topleft)

    @staticmethod
    def handle_click(
        surface: pygame.Surface, pos: tuple[int, int], resources: ResourceManager
    ) -> None:
        if resources.get("wood") < BUILD_COST_WOOD:
            return
        for rect, _asset_key, tag in _button_rects(surface):
            if rect.collidepoint(pos):
                pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type=tag))
                return
