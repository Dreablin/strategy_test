"""Fixed-height top HUD strip for resources and per-cycle income."""

import pygame

from game.assets import resource_icon
from game.resources import ResourceManager

_BAR_HEIGHT = 48
_RESOURCE_ORDER: tuple[str, ...] = ("food", "wood", "stone", "iron")


class TopBar:
    """48 px strip: `[icon] amount (+income)` for each resource, left to right."""

    @staticmethod
    def draw(surface: pygame.Surface, resources: ResourceManager) -> None:
        width = surface.get_width()
        strip = pygame.Rect(0, 0, width, _BAR_HEIGHT)
        pygame.draw.rect(surface, (32, 36, 44), strip)
        pygame.draw.line(surface, (56, 60, 68), (0, _BAR_HEIGHT - 1), (width, _BAR_HEIGHT - 1))

        income = resources.per_cycle
        col_w = max(1, width // len(_RESOURCE_ORDER))
        font = pygame.font.Font(None, 22)

        for i, name in enumerate(_RESOURCE_ORDER):
            x0 = i * col_w + 6
            icon = resource_icon(name)
            icon_y = (_BAR_HEIGHT - icon.get_height()) // 2
            surface.blit(icon, (x0, icon_y))

            text_x = x0 + icon.get_width() + 6
            amount = resources.get(name)
            inc = int(income.get(name, 0))
            label = f"{amount}  (+{inc})"
            text_surf = font.render(label, True, (228, 230, 238))
            text_y = (_BAR_HEIGHT - text_surf.get_height()) // 2
            surface.blit(text_surf, (text_x, text_y))
