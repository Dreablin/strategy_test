"""Fixed-height bottom strip with category/submenu build tools."""

from __future__ import annotations

import pygame

from game.assets import building_sprite, resource_icon
from game.config import CONSTRUCTION_REQUIREMENTS
from game.research_config import RESEARCH_BY_ID
from game.resource_catalog import resource_display_label
from game.statue_research import statue_stage_research_id

BAR_HEIGHT = 96
# Distinct from other user events; carries `building_type: str` (e.g. `"LUMBER_CAMP"`).
BUILD_MENU_SELECT = pygame.USEREVENT + 10

_RESOURCE_BUTTONS: tuple[tuple[str, str, str], ...] = (
    ("lumber_camp", "Lumber", "LUMBER_CAMP"),
    ("stone_mine", "Stone", "STONE_MINE"),
    ("iron_mine", "Iron", "IRON_MINE"),
    ("forester_hut", "Forester", "FORESTER_HUT"),
    ("well", "Well", "WELL"),
)
_FOOD_BUTTONS: tuple[tuple[str, str, str], ...] = (
    ("farm", "Farm", "FARM"),
    ("field", "Field", "FIELD"),
    ("vineyard_farm", "Vineyard Farm", "VINEYARD_FARM"),
    ("vineyard", "Vineyard", "VINEYARD"),
)
# Backward-compat for tests importing previous flat menu tuple.
_BUTTONS = _RESOURCE_BUTTONS

_TOOLTIP_PAD = 8
_TOOLTIP_GAP = 4
_TOOLTIP_BG = (22, 26, 34)
_TOOLTIP_BORDER = (72, 78, 92)
_TOOLTIP_TEXT = (220, 224, 232)


def _button_rects(surface: pygame.Surface, count: int) -> list[pygame.Rect]:
    w, h = surface.get_width(), surface.get_height()
    y0 = h - BAR_HEIGHT
    col_w = max(1, w // max(1, count))
    return [pygame.Rect(i * col_w, y0, col_w, BAR_HEIGHT) for i in range(count)]


def _building_entries_for_menu(menu: str) -> tuple[tuple[str, str], ...]:
    if menu == "resource":
        return tuple((tag, label) for _asset, label, tag in _RESOURCE_BUTTONS)
    if menu == "food":
        return tuple((tag, label) for _asset, label, tag in _FOOD_BUTTONS)
    if menu == "social":
        return (
            ("SCHOOL", "School"),
            ("HOUSE", "House"),
            ("CANTEEN", "Canteen"),
            ("RESTAURANT", "Restaurant"),
            ("LABORATORY", "Laboratory"),
            ("STATUE", "Statue"),
        )
    if menu == "processing":
        return (
            ("SAWMILL", "Sawmill"),
            ("MILL", "Mill"),
            ("BAKERY", "Bakery"),
            ("CHICKEN_FARM", "Chicken Farm"),
            ("COW_FARM", "Cow Farm"),
            ("WINERY", "Winery"),
        )
    return ()


def _hovered_building_tag(surface: pygame.Surface, pos: tuple[int, int] | None) -> str | None:
    if pos is None:
        return None
    menu = BottomBar._menu
    entries = _building_entries_for_menu(menu)
    if not entries:
        return None
    x, y = pos
    if y < surface.get_height() - BAR_HEIGHT:
        return None
    rects = _button_rects(surface, len(entries) + 1)
    for rect, (tag, _label) in zip(rects[1:], entries):
        if rect.collidepoint(x, y):
            return tag
    return None


def _construction_cost_lines(building_tag: str) -> tuple[str, ...]:
    spec = CONSTRUCTION_REQUIREMENTS.get(building_tag, {}).get(1)
    if spec is None:
        lines = ["Cost: unavailable"]
    else:
        items = [(resource, amount) for resource, amount in sorted(spec.cost.items()) if int(amount) > 0]
        if not items:
            lines = ["Cost: Free"]
        else:
            lines = ["Cost:"]
            for resource, amount in items:
                lines.append(f"{resource_display_label(resource)}: {int(amount)}")
    if building_tag == "STATUE":
        research_id = statue_stage_research_id(1)
        if research_id is not None:
            research = RESEARCH_BY_ID.get(research_id)
            name = research.name if research is not None else research_id
            lines.append(f"Requires research: {name}")
    return tuple(lines)


def _draw_building_cost_tooltip(
    surface: pygame.Surface,
    hover_pos: tuple[int, int] | None,
) -> pygame.Rect | None:
    tag = _hovered_building_tag(surface, hover_pos)
    if tag is None or hover_pos is None:
        return None
    font = pygame.font.Font(None, 18)
    line_surfaces = [font.render(line, True, _TOOLTIP_TEXT) for line in _construction_cost_lines(tag)]
    max_w = max(surf.get_width() for surf in line_surfaces)
    total_h = sum(surf.get_height() for surf in line_surfaces) + _TOOLTIP_GAP * (len(line_surfaces) - 1)
    box_w = max_w + _TOOLTIP_PAD * 2
    box_h = total_h + _TOOLTIP_PAD * 2
    x = max(4, min(hover_pos[0] + 12, surface.get_width() - box_w - 4))
    y = max(4, surface.get_height() - BAR_HEIGHT - box_h - 8)
    box = pygame.Rect(x, y, box_w, box_h)
    pygame.draw.rect(surface, _TOOLTIP_BG, box, border_radius=4)
    pygame.draw.rect(surface, _TOOLTIP_BORDER, box, width=1, border_radius=4)
    line_y = box.top + _TOOLTIP_PAD
    for surf in line_surfaces:
        surface.blit(surf, (box.left + _TOOLTIP_PAD, line_y))
        line_y += surf.get_height() + _TOOLTIP_GAP
    return box


class BottomBar:
    """Category-driven build strip with submenu navigation."""
    _menu: str = "main"  # main | resource | processing | dev

    @staticmethod
    def back_to_main() -> bool:
        """Return from a submenu to the main build menu."""
        if BottomBar._menu == "main":
            return False
        BottomBar._menu = "main"
        return True

    @staticmethod
    def draw(surface: pygame.Surface, hover_pos: tuple[int, int] | None = None) -> None:
        w, h = surface.get_width(), surface.get_height()
        y0 = h - BAR_HEIGHT
        pygame.draw.rect(surface, (26, 28, 34), (0, y0, w, BAR_HEIGHT))
        pygame.draw.line(surface, (48, 52, 60), (0, y0), (w, y0))

        font = pygame.font.Font(None, 22)
        menu = BottomBar._menu
        if menu == "main":
            entries: tuple[tuple[str, str], ...] = (
                ("resource", "Resource"),
                ("food", "Food"),
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
            _draw_building_cost_tooltip(surface, hover_pos)
            return

        if menu == "food":
            entries = (("back", "Back", ""),) + _FOOD_BUTTONS
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
                spr = pygame.transform.smoothscale(building_sprite(asset_key, 1), (44, 34))
                surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 42))
                text = font.render(label, True, (220, 222, 230))
                surface.blit(text, (btn.centerx - text.get_width() // 2, btn.top + 10))
            _draw_building_cost_tooltip(surface, hover_pos)
            return

        if menu == "social":
            entries = (
                ("back", "Back"),
                ("school", "School"),
                ("house", "House"),
                ("canteen", "Canteen"),
                ("restaurant", "Restaurant"),
                ("laboratory", "Laboratory"),
                ("statue", "Statue"),
            )
            rects = _button_rects(surface, len(entries))
            for rect, (key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(text, (btn.centerx - text.get_width() // 2, btn.top + 10))
                if key == "school":
                    spr = pygame.transform.smoothscale(building_sprite("school", 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
                elif key == "house":
                    spr = pygame.transform.smoothscale(building_sprite("house", 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
                elif key == "canteen":
                    spr = pygame.transform.smoothscale(building_sprite("canteen", 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
                elif key == "restaurant":
                    spr = pygame.transform.smoothscale(building_sprite("restaurant", 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
                elif key == "laboratory":
                    spr = pygame.transform.smoothscale(building_sprite("laboratory", 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
                elif key == "statue":
                    spr = pygame.transform.smoothscale(building_sprite("statue", 4), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
            _draw_building_cost_tooltip(surface, hover_pos)
            return

        if menu == "processing":
            entries = (
                ("back", "Back"),
                ("sawmill", "Sawmill"),
                ("mill", "Mill"),
                ("bakery", "Bakery"),
                ("chicken_farm", "Chicken Farm"),
                ("cow_farm", "Cow Farm"),
                ("winery", "Winery"),
            )
            rects = _button_rects(surface, len(entries))
            for rect, (_key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(
                    text,
                    (btn.centerx - text.get_width() // 2, btn.centery - text.get_height() // 2),
                )
            for idx, asset_key in (
                (1, "sawmill"),
                (2, "mill"),
                (3, "bakery"),
                (4, "chicken_farm"),
                (5, "cow_farm"),
                (6, "winery"),
            ):
                spr = pygame.transform.smoothscale(building_sprite(asset_key, 1), (40, 32))
                btn = rects[idx].inflate(-6, -10)
                surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
            _draw_building_cost_tooltip(surface, hover_pos)
            return

        if menu == "dev":
            entries = (("back", "Back"), ("tree", "Tree"), ("stone", "Stone"), ("iron", "Iron"))
            rects = _button_rects(surface, len(entries))
            for rect, (key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(text, (btn.centerx - text.get_width() // 2, btn.top + 10))
                if key in {"tree", "stone", "iron"}:
                    resource_key = {"tree": "wood", "stone": "stone", "iron": "iron"}[key]
                    icon = pygame.transform.smoothscale(resource_icon(resource_key), (20, 20))
                    surface.blit(icon, (btn.centerx - 10, btn.bottom - 28))
            _draw_building_cost_tooltip(surface, hover_pos)
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
            fg = (220, 222, 230)
            name_s = font.render(label, True, fg)
            tx = sx + spr.get_width() + 8
            ty_name = inner.top + 8
            surface.blit(name_s, (tx, ty_name))
        _draw_building_cost_tooltip(surface, hover_pos)

    @staticmethod
    def handle_click(surface: pygame.Surface, pos: tuple[int, int]) -> None:
        menu = BottomBar._menu
        if menu == "main":
            entries = ("resource", "food", "social", "processing", "dev")
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if rect.collidepoint(pos):
                    BottomBar._menu = key
                    return
            return

        if menu == "food":
            entries = (("back", "Back", ""),) + _FOOD_BUTTONS
            for rect, (_asset_key, _label, tag) in zip(_button_rects(surface, len(entries)), entries):
                if not rect.collidepoint(pos):
                    continue
                if tag == "":
                    BottomBar._menu = "main"
                    return
                pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type=tag))
                return
            return

        if menu == "social":
            entries = ("back", "school", "house", "canteen", "restaurant", "laboratory", "statue")
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if not rect.collidepoint(pos):
                    continue
                if key == "back":
                    BottomBar._menu = "main"
                elif key == "school":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="SCHOOL"))
                elif key == "house":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="HOUSE"))
                elif key == "canteen":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="CANTEEN"))
                elif key == "restaurant":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="RESTAURANT"))
                elif key == "laboratory":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="LABORATORY"))
                elif key == "statue":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="STATUE"))
                return
            return

        if menu == "processing":
            entries = (
                "back",
                "sawmill",
                "mill",
                "bakery",
                "chicken_farm",
                "cow_farm",
                "winery",
            )
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if not rect.collidepoint(pos):
                    continue
                if key == "back":
                    BottomBar._menu = "main"
                elif key == "sawmill":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="SAWMILL"))
                elif key == "mill":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="MILL"))
                elif key == "bakery":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="BAKERY"))
                elif key == "chicken_farm":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="CHICKEN_FARM"))
                elif key == "cow_farm":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="COW_FARM"))
                elif key == "winery":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="WINERY"))
                return
            return

        if menu == "dev":
            entries = ("back", "tree", "stone", "iron")
            for rect, key in zip(_button_rects(surface, len(entries)), entries):
                if not rect.collidepoint(pos):
                    continue
                if key == "back":
                    BottomBar._menu = "main"
                elif key == "tree":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_TREE"))
                elif key == "stone":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_STONE"))
                elif key == "iron":
                    pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_IRON"))
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
            pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type=tag))
            return
