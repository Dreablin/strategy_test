"""Fixed-height bottom strip with category/submenu build tools."""

from __future__ import annotations

import pygame

from game import i18n
from game.assets import building_sprite, resource_icon
from game.config import CONSTRUCTION_REQUIREMENTS
from game.research_config import RESEARCH_BY_ID
from game.resource_catalog import resource_display_label
from game.statue_research import statue_stage_research_id
from game.ui.building_panel import building_display_name
from game.ui.fonts import ui_font

BAR_HEIGHT = 96
# Distinct from other user events; carries `building_type: str` (e.g. `"LUMBER_CAMP"`).
BUILD_MENU_SELECT = pygame.USEREVENT + 10

_RESOURCE_BUTTON_SPECS: tuple[tuple[str, str], ...] = (
    ("lumber_camp", "LUMBER_CAMP"),
    ("stone_mine", "STONE_MINE"),
    ("iron_mine", "IRON_MINE"),
    ("forester_hut", "FORESTER_HUT"),
    ("well", "WELL"),
)
_FOOD_BUTTON_SPECS: tuple[tuple[str, str], ...] = (
    ("farm", "FARM"),
    ("field", "FIELD"),
    ("vineyard_farm", "VINEYARD_FARM"),
    ("vineyard", "VINEYARD"),
)
# Backward-compat for tests importing previous flat menu tuple (asset, type_tag).
_RESOURCE_BUTTONS = _RESOURCE_BUTTON_SPECS
_FOOD_BUTTONS = _FOOD_BUTTON_SPECS
_BUTTONS = _RESOURCE_BUTTONS

_SOCIAL_BUILDING_TAGS: tuple[str, ...] = (
    "SCHOOL",
    "HOUSE",
    "CANTEEN",
    "RESTAURANT",
    "LABORATORY",
    "STATUE",
)
_PROCESSING_BUILDING_TAGS: tuple[str, ...] = (
    "SAWMILL",
    "MILL",
    "BAKERY",
    "CHICKEN_FARM",
    "COW_FARM",
    "WINERY",
)

_TOOLTIP_PAD = 8
_TOOLTIP_GAP = 4
_TOOLTIP_BG = (22, 26, 34)
_TOOLTIP_BORDER = (72, 78, 92)
_TOOLTIP_TEXT = (220, 224, 232)


def _labeled_menu_buttons(
    specs: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple((asset, building_display_name(tag), tag) for asset, tag in specs)


def _back_button_label() -> str:
    return i18n.t("ui.button.back")


def _main_menu_entries() -> tuple[tuple[str, str], ...]:
    return (
        ("resource", i18n.t("ui.bottom_bar.category.resource")),
        ("food", i18n.t("ui.bottom_bar.category.food")),
        ("social", i18n.t("ui.bottom_bar.category.social")),
        ("processing", i18n.t("ui.bottom_bar.category.processing")),
        ("dev", i18n.t("ui.bottom_bar.category.dev")),
    )


def _dev_menu_entries() -> tuple[tuple[str, str], ...]:
    return (
        ("back", _back_button_label()),
        ("tree", i18n.t("ui.bottom_bar.dev.tree")),
        ("stone", i18n.t("ui.bottom_bar.dev.stone")),
        ("iron", i18n.t("ui.bottom_bar.dev.iron")),
    )


def _button_rects(surface: pygame.Surface, count: int) -> list[pygame.Rect]:
    w, h = surface.get_width(), surface.get_height()
    y0 = h - BAR_HEIGHT
    col_w = max(1, w // max(1, count))
    return [pygame.Rect(i * col_w, y0, col_w, BAR_HEIGHT) for i in range(count)]


def _building_entries_for_menu(menu: str) -> tuple[tuple[str, str], ...]:
    if menu == "resource":
        return tuple((tag, building_display_name(tag)) for _asset, tag in _RESOURCE_BUTTON_SPECS)
    if menu == "food":
        return tuple((tag, building_display_name(tag)) for _asset, tag in _FOOD_BUTTON_SPECS)
    if menu == "social":
        return tuple((tag, building_display_name(tag)) for tag in _SOCIAL_BUILDING_TAGS)
    if menu == "processing":
        return tuple((tag, building_display_name(tag)) for tag in _PROCESSING_BUILDING_TAGS)
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
    cost_label = i18n.t("ui.common.cost")
    spec = CONSTRUCTION_REQUIREMENTS.get(building_tag, {}).get(1)
    if spec is None:
        lines = [f"{cost_label}: {i18n.t('ui.common.unavailable')}"]
    else:
        items = [(resource, amount) for resource, amount in sorted(spec.cost.items()) if int(amount) > 0]
        if not items:
            lines = [f"{cost_label}: {i18n.t('ui.common.free')}"]
        else:
            lines = [f"{cost_label}:"]
            for resource, amount in items:
                lines.append(f"{resource_display_label(resource)}: {int(amount)}")
    if building_tag == "STATUE":
        research_id = statue_stage_research_id(1)
        if research_id is not None:
            research = RESEARCH_BY_ID.get(research_id)
            name = research.name if research is not None else research_id
            lines.append(i18n.t("ui.common.requires_research", name=name))
    return tuple(lines)


def _draw_building_cost_tooltip(
    surface: pygame.Surface,
    hover_pos: tuple[int, int] | None,
) -> pygame.Rect | None:
    tag = _hovered_building_tag(surface, hover_pos)
    if tag is None or hover_pos is None:
        return None
    font = ui_font(18)
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

        font = ui_font(22)
        menu = BottomBar._menu
        if menu == "main":
            entries = _main_menu_entries()
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
            entries = (("back", _back_button_label(), ""),) + _labeled_menu_buttons(_FOOD_BUTTON_SPECS)
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
            social_assets = {
                "SCHOOL": "school",
                "HOUSE": "house",
                "CANTEEN": "canteen",
                "RESTAURANT": "restaurant",
                "LABORATORY": "laboratory",
                "STATUE": "statue",
            }
            entries = (("back", _back_button_label()),) + tuple(
                (tag.lower(), building_display_name(tag)) for tag in _SOCIAL_BUILDING_TAGS
            )
            rects = _button_rects(surface, len(entries))
            for rect, (key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(text, (btn.centerx - text.get_width() // 2, btn.top + 10))
                asset_key = social_assets.get(key.upper())
                if asset_key is not None:
                    level = 4 if asset_key == "statue" else 1
                    spr = pygame.transform.smoothscale(building_sprite(asset_key, level), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
            _draw_building_cost_tooltip(surface, hover_pos)
            return

        if menu == "processing":
            processing_assets = {
                "SAWMILL": "sawmill",
                "MILL": "mill",
                "BAKERY": "bakery",
                "CHICKEN_FARM": "chicken_farm",
                "COW_FARM": "cow_farm",
                "WINERY": "winery",
            }
            entries = (("", _back_button_label()),) + tuple(
                (processing_assets[tag], building_display_name(tag)) for tag in _PROCESSING_BUILDING_TAGS
            )
            rects = _button_rects(surface, len(entries))
            for rect, (asset_key, label) in zip(rects, entries):
                btn = rect.inflate(-6, -10)
                pygame.draw.rect(surface, (36, 40, 48), btn, border_radius=6)
                text = font.render(label, True, (220, 222, 230))
                surface.blit(
                    text,
                    (btn.centerx - text.get_width() // 2, btn.centery - text.get_height() // 2),
                )
                if asset_key:
                    spr = pygame.transform.smoothscale(building_sprite(asset_key, 1), (40, 32))
                    surface.blit(spr, (btn.centerx - spr.get_width() // 2, btn.bottom - 40))
            _draw_building_cost_tooltip(surface, hover_pos)
            return

        if menu == "dev":
            entries = _dev_menu_entries()
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
        entries = (("back", _back_button_label(), ""),) + _labeled_menu_buttons(_RESOURCE_BUTTON_SPECS)
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
            entries = (("back", _back_button_label(), ""),) + _labeled_menu_buttons(_FOOD_BUTTON_SPECS)
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
        entries = (("back", _back_button_label(), ""),) + _labeled_menu_buttons(_RESOURCE_BUTTON_SPECS)
        for rect, (_asset_key, _label, tag) in zip(_button_rects(surface, len(entries)), entries):
            if not rect.collidepoint(pos):
                continue
            if tag == "":
                BottomBar._menu = "main"
                return
            pygame.event.post(pygame.event.Event(BUILD_MENU_SELECT, building_type=tag))
            return
