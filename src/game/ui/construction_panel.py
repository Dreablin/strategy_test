"""Construction-specific modal panel for under-construction buildings."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets import resource_icon
from game.buildings.base import Building

_PANEL_W = 460
_PANEL_PAD = 16
_ROW = 26
_CLOSE = 28
_BAR_H = 16
_BTN_H = 36

_DISPLAY_NAME: dict[str, str] = {
    "TOWN_HALL": "Town Hall",
    "LUMBER_CAMP": "Lumber Camp",
    "STONE_MINE": "Stone Mine",
    "IRON_MINE": "Iron Mine",
    "FARM": "Farm",
    "FORESTER_HUT": "Forester Hut",
    "SCHOOL": "School",
    "HOUSE": "House",
    "BAKERY": "Bakery",
    "CANTEEN": "Canteen",
    "WELL": "Well",
    "VINEYARD": "Vineyard",
    "LABORATORY": "Laboratory",
    "STATUE": "Statue",
}


@dataclass(frozen=True, slots=True)
class ConstructionPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    demolish: pygame.Rect | None
    toggle: pygame.Rect | None


class ConstructionPanel:
    @staticmethod
    def layout(surface: pygame.Surface, building: Building) -> ConstructionPanelLayout:
        site = building.construction_site
        if site is None:
            raise ValueError("construction panel requires building.construction_site")
        rows = max(1, len(site.required_resources))
        progress_rows = 2 if site.is_building() else 0
        can_demolish = building.type_tag != "STATUE"
        has_toggle = building.type_tag == "STATUE"
        button_count = int(can_demolish) + int(has_toggle)
        h = _PANEL_PAD * 2 + _ROW + (3 + rows + progress_rows) * _ROW + button_count * (_BTN_H + 8) + 18
        sw, sh = surface.get_size()
        frame = pygame.Rect(sw // 2 - _PANEL_W // 2, sh // 2 - h // 2, _PANEL_W, h)
        close = pygame.Rect(
            frame.right - _PANEL_PAD - _CLOSE,
            frame.top + _PANEL_PAD,
            _CLOSE,
            _CLOSE,
        )
        y = frame.bottom - _PANEL_PAD - _BTN_H
        toggle = None
        demolish = None
        if has_toggle:
            toggle = pygame.Rect(
                frame.left + _PANEL_PAD,
                y,
                frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )
            y -= _BTN_H + 8
        if can_demolish:
            demolish = pygame.Rect(
                frame.left + _PANEL_PAD,
                y,
                frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )
        return ConstructionPanelLayout(frame=frame, close=close, demolish=demolish, toggle=toggle)

    @staticmethod
    def title_line(building: Building) -> str:
        site = building.construction_site
        if site is None:
            return "Under Construction"
        current_stage = getattr(building, "current_construction_stage_name", None)
        if callable(current_stage):
            return f"Building: {current_stage()}"
        if int(site.target_level) > int(building.level):
            return f"Upgrading to Lv {int(site.target_level)}"
        return "Under Construction"

    @staticmethod
    def builder_status(building: Building) -> str:
        site = building.construction_site
        if site is None:
            return "Waiting for resources"
        if not site.is_fully_supplied():
            return "Waiting for resources"
        if not site.is_building():
            return "Waiting for builder"
        return "Building..."

    @staticmethod
    def draw(surface: pygame.Surface, building: Building, *, now_ms: int) -> None:
        site = building.construction_site
        if site is None:
            return
        layout = ConstructionPanel.layout(surface, building)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)

        title_font = pygame.font.Font(None, 28)
        body_font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 20)

        name = _DISPLAY_NAME.get(building.type_tag, building.type_tag)
        title = title_font.render(f"{name} — {ConstructionPanel.title_line(building)}", True, (238, 240, 248))
        surface.blit(title, (layout.frame.left + _PANEL_PAD, layout.frame.top + _PANEL_PAD))

        pygame.draw.line(
            surface,
            (200, 82, 82),
            (layout.close.left + 6, layout.close.top + 6),
            (layout.close.right - 7, layout.close.bottom - 7),
            2,
        )
        pygame.draw.line(
            surface,
            (200, 82, 82),
            (layout.close.right - 7, layout.close.top + 6),
            (layout.close.left + 6, layout.close.bottom - 7),
            2,
        )

        y = layout.frame.top + _PANEL_PAD + _ROW + 6
        surface.blit(body_font.render("Requirements:", True, (205, 210, 220)), (layout.frame.left + _PANEL_PAD, y))
        y += _ROW
        for resource, required in site.required_resources.items():
            delivered = int(site.delivered_resources.get(resource, 0))
            icon = pygame.transform.smoothscale(resource_icon(resource), (18, 18))
            surface.blit(icon, (layout.frame.left + _PANEL_PAD, y + 3))
            line = f"{resource.capitalize()}: {delivered}/{int(required)}"
            surface.blit(small_font.render(line, True, (205, 210, 220)), (layout.frame.left + _PANEL_PAD + 24, y))
            y += _ROW

        surface.blit(
            body_font.render(f"Builder: {ConstructionPanel.builder_status(building)}", True, (205, 210, 220)),
            (layout.frame.left + _PANEL_PAD, y),
        )
        y += _ROW
        if site.is_building():
            progress = max(0.0, min(1.0, site.build_progress(int(now_ms))))
            pct = int(round(progress * 100))
            surface.blit(
                body_font.render(f"Progress: {pct}%", True, (205, 210, 220)),
                (layout.frame.left + _PANEL_PAD, y),
            )
            y += _ROW
            bar_w = layout.frame.width - _PANEL_PAD * 2
            bar = pygame.Rect(layout.frame.left + _PANEL_PAD, y + 4, bar_w, _BAR_H)
            fill = pygame.Rect(bar.left, bar.top, int(bar.width * progress), bar.height)
            pygame.draw.rect(surface, (52, 56, 64), bar, border_radius=6)
            pygame.draw.rect(surface, (224, 194, 80), fill, border_radius=6)
            pygame.draw.rect(surface, (92, 98, 112), bar, width=1, border_radius=6)

        btn_font = pygame.font.Font(None, 24)
        if layout.demolish is not None:
            pygame.draw.rect(surface, (140, 48, 52), layout.demolish, border_radius=6)
            dl = btn_font.render("Demolish", True, (255, 240, 240))
            surface.blit(
                dl,
                (
                    layout.demolish.centerx - dl.get_width() // 2,
                    layout.demolish.centery - dl.get_height() // 2,
                ),
            )
        if layout.toggle is not None:
            enabled = bool(getattr(building, "construction_deliveries_enabled", True))
            bg = (84, 112, 84) if enabled else (92, 64, 64)
            pygame.draw.rect(surface, bg, layout.toggle, border_radius=6)
            label = btn_font.render(
                "Deliveries Active" if enabled else "Deliveries Paused",
                True,
                (240, 242, 250),
            )
            surface.blit(
                label,
                (
                    layout.toggle.centerx - label.get_width() // 2,
                    layout.toggle.centery - label.get_height() // 2,
                ),
            )

    @staticmethod
    def click_action(surface: pygame.Surface, pos: tuple[int, int], building: Building) -> str | None:
        layout = ConstructionPanel.layout(surface, building)
        if layout.close.collidepoint(pos):
            return "close"
        if layout.demolish is not None and layout.demolish.collidepoint(pos):
            return "demolish"
        if layout.toggle is not None and layout.toggle.collidepoint(pos):
            return "toggle_construction_deliveries"
        return None
