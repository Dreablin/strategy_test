"""Winery panel with storage rows, progress bar, and active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.winery import Winery
from game.ui.building_panel import BuildingPanel
from game.ui.fonts import ui_font

_PANEL_PAD = 16
_BTN_H = 32
_ROW_H = 22
_BAR_H = 12
_EXTRA_BOTTOM = _ROW_H * 3 + _BAR_H + 24 + _BTN_H + 8
_DETAILS_GAP = 12
_DETAILS_H = _ROW_H * 3 + 4 + _BAR_H


@dataclass(frozen=True, slots=True)
class WineryPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class WineryPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, Winery)

    @staticmethod
    def toggle_label(winery: Winery) -> str:
        return "Active" if winery.active else "Inactive"

    @staticmethod
    def storage_lines(winery: Winery) -> tuple[str, str]:
        grapes_line = f"Grapes: {winery.input_amount()} / {winery.input_capacity()}"
        wine_line = f"Wine: {winery.output_amount()} / {winery.output_capacity()}"
        return grapes_line, wine_line

    @staticmethod
    def details_top(layout: WineryPanelLayout) -> int:
        action_tops = [layout.toggle.top]
        if layout.upgrade is not None:
            action_tops.append(layout.upgrade.top)
        if layout.demolish is not None:
            action_tops.append(layout.demolish.top)
        return min(action_tops) - _DETAILS_GAP - _DETAILS_H

    @staticmethod
    def layout(
        surface: pygame.Surface,
        winery: Winery,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> WineryPanelLayout:
        base = BuildingPanel.layout(
            surface,
            winery,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        toggle = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - _BTN_H,
            base.frame.width - _PANEL_PAD * 2,
            _BTN_H,
        )
        return WineryPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=base.upgrade,
            upgrade_enabled=base.upgrade_enabled,
            demolish=base.demolish,
            toggle=toggle,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        winery: Winery,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int,
    ) -> None:
        BuildingPanel.draw(
            surface,
            winery,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = WineryPanel.layout(
            surface,
            winery,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = ui_font(22)

        grapes_line, wine_line = WineryPanel.storage_lines(winery)
        y = WineryPanel.details_top(layout)
        surface.blit(font.render(grapes_line, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        y += _ROW_H
        surface.blit(font.render(wine_line, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        y += _ROW_H

        status_text = production_status or "Idle"
        surface.blit(font.render(f"Production: {status_text}", True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        y += _ROW_H + 4

        bar_rect = pygame.Rect(layout.frame.left + _PANEL_PAD, y, layout.frame.width - _PANEL_PAD * 2, _BAR_H)
        pygame.draw.rect(surface, (52, 58, 66), bar_rect, border_radius=4)
        progress = max(0.0, min(1.0, float(winery.processing_progress(now_ms))))
        if progress > 0.0:
            fill = pygame.Rect(bar_rect.left, bar_rect.top, max(1, int(round(bar_rect.width * progress))), bar_rect.height)
            pygame.draw.rect(surface, (130, 72, 100), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_rect, width=1, border_radius=4)

        active_bg = (84, 112, 84) if winery.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(WineryPanel.toggle_label(winery), True, (240, 242, 250))
        surface.blit(label, (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2))

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        winery: Winery,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            winery,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = WineryPanel.layout(
            surface,
            winery,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
