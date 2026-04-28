"""Fixed-height bottom strip with category/submenu build tools."""

from __future__ import annotations

import pygame

from game.assets import building_sprite, resource_icon
from game.buildings.costs import build_cost
from game.resources import ResourceManager

BAR_HEIGHT = 96
# Distinct from other user events; carries `building_type: str` (e.g. `"LUMBER_CAMP"`).
BUILD_MENU_SELECT = pygame.USEREVENT + 10

_RESOURCE_BUTTONS: tuple[tuple[str, str, str], ...] = (
    ("lumber_camp", "Lumber", "LUMBER_CAMP"),
    ("stone_mine", "Stone", "STONE_MINE"),
    ("iron_mine", "Iron", "IRON_MINE"),
    ("farm", "Farm", "FARM"),
    ("forester_hut", "Forester", "FORESTER_HUT"),
)
# Backward-compat for tests importing previous flat menu tuple.
_BUTTONS = _RESOURCE_BUTTONS


def _button_rects(surface: pygame.Surface, count: int) -> list[pygame.Rect]:
    w, h = surface.get_width(), surface.get_height()
    y0 = h - BAR_HEIGHT
    col_w = max(1, w // max(1, count))
    return [pygame.Rect(i * col_w, y0, col_w, BAR_HEIGHT) for i in range(count)]


class BottomBar:
    """Category-driven build strip with submenu navigation."""
    _menu: str = "main"  # main | resource | processing | dev

    @staticmethod
    def draw(surface: pygame.Surface, resources: ResourceManager) -> None:
        w, h = surface.get_width(), surface.get_height()
        y0 = h - BAR_HEIGHT
        pygame.draw.rect(surface, (26, 28, 34), (0, y0, w, BAR_HEIGHT))
        pygame.draw.line(surface, (48, 52, 60), (0, y0), (w, y0))

        font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 18)
        menu = BottomBar._menu
        if menu == "main":
            entries: tuple[tuple[str, str], ...] = (
                ("resource", "Resource"),
                ("social", "Social"),
                ("processing", "Processing"),
                ("dev", "Dev"),
            )
            for rect, (_key, label) in zip(_button_rects(surface, len(entries)), entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(
                    text,
                    (btn.centerx - text.get_width() // 2, btn.centery - text.get_height() // 2),
                )
            return

        if menu == "social":
            entries = (("back", "Back"), ("school", "School"))
            rects = _button_rects(surface, len(entries))
            for rect, (key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(text, (btn.centerx - text.get_width() // 2, btn.top + 10))
                if key == "school":
                    spr = pygame.transform.smoothscale(building_sprite("school", 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
            return

        if menu == "processing":
            entries = (("back", "Back"),)
            for rect, (_key, label) in zip(_button_rects(surface, len(entries)), entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(
                    text,
                    (btn.centerx - text.get_width() // 2, btn.centery - text.get_height() // 2),
                )
            msg = small_font.render("Processing: empty", True, (150, 156, 170))
            surface.blit(msg, (w // 2 - msg.get_width() // 2, y0 + 8))
            return

        if menu == "dev":
            entries = (("back", "Back"), ("tree", "Tree"), ("stone", "Stone"))
            rects = _button_rects(surface, len(entries))
            for rect, (key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(text, (btn.centerx - text.get_width() // 2, btn.top + 10))
                if key in {"tree", "stone"}:
                    icon = pygame.transform.smoothscale(resource_icon("wood" if key == "tree" else "stone"), (20, 20))
                    surface.blit(icon, (btn.centerx - 10, btn.bottom - 28))
            return

        # resource submenu
        entries = (("back", "Back", ""),) + _RESOURCE_BUTTONS
        rects = _button_rects(surface, len(entries))
        for rect, (asset_key, label, tag) in zip(rects, entries):
            btn = rect.inflate(-6, -10)
            pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
            if tag == "":
                text = font.render(label, True, (220, 222, 230))
                surface.blit(
                    text,
                    (btn.centerx - text.get_width() // 2, btn.centery - text.get_height() // 2),
                )
                continue
            inner = rect.inflate(-12, -14)
            spr = pygame.transform.smoothscale(
                building_sprite(asset_key, 1),
                (min(56, inner.width // 3), min(48, inner.height - 28)),
            )
            sx = inner.left + 8
            sy = inner.centery - spr.get_height() // 2
            surface.blit(spr, (sx, sy))
            cost = build_cost(tag)
            cost_wood = int(cost.get("wood", 0))
            can_afford = resources.get("wood") >= cost_wood
            fg = (220, 222, 230) if can_afford else (110, 112, 120)
            name_s = font.render(label, True, fg)
            tx = sx + spr.get_width() + 8
            ty_name = inner.top + 8
            surface.blit(name_s, (tx, ty_name))
            cost_y = ty_name + name_s.get_height() + 4
            cost_s = small_font.render(str(cost_wood), True, fg)
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
        menu = BottomBar._menu
        if menu == "main":
            entries = ("resource", "social", "processing", "dev")
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if rect.collidepoint(pos):
                    BottomBar._menu = key
                    return
            return

        if menu == "social":
            entries = ("back", "school")
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if not rect.collidepoint(pos):
                    continue
                if key == "back":
                    BottomBar._menu = "main"
                else:
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="SCHOOL"))
                return
            return

        if menu == "processing":
            rects = _button_rects(surface, 1)
            if rects and rects[0].collidepoint(pos):
                BottomBar._menu = "main"
            return

        if menu == "dev":
            entries = ("back", "tree", "stone")
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if not rect.collidepoint(pos):
                    continue
                if key == "back":
                    BottomBar._menu = "main"
                elif key == "tree":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_TREE"))
                elif key == "stone":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_STONE"))
                return
            return

        # resource submenu
        entries = (("back", "Back", ""),) + _RESOURCE_BUTTONS
        for rect, (_asset_key, _label, tag) in zip(_button_rects(surface, len(entries)), entries):
            if not rect.collidepoint(pos):
                continue
            if tag == "":
                BottomBar._menu = "main"
                return
            cost_wood = int(build_cost(tag).get("wood", 0))
            if resources.get("wood") < cost_wood:
                return
            pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type=tag))
            return
