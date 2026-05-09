"""Well panel with local water storage, worker status, and active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.well import Well
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 112


@dataclass(frozen=True, slots=True)
class WellPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class WellPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, Well)

    @staticmethod
    def toggle_label(well: Well) -> str:
        return "Active" if well.active else "Inactive"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        well: Well,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> WellPanelLayout:
        base = BuildingPanel.layout(
            surface,
            well,
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
        return WellPanelLayout(
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
        well: Well,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int,
    ) -> None:
        BuildingPanel.draw(
            surface,
            well,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = WellPanel.layout(
            surface,
            well,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )

        font = pygame.font.Font(None, 22)
        bar_y = layout.frame.top + _PANEL_PAD + 4 * 26 + 30
        bar_bg = pygame.Rect(layout.frame.left + _PANEL_PAD, bar_y, layout.frame.width - _PANEL_PAD * 2, 12)
        pygame.draw.rect(surface, (52, 58, 66), bar_bg, border_radius=4)
        progress = max(0.0, min(1.0, float(well.processing_progress(now_ms))))
        if progress > 0.0:
            fill = pygame.Rect(bar_bg.left, bar_bg.top, max(1, int(round(bar_bg.width * progress))), bar_bg.height)
            pygame.draw.rect(surface, (92, 146, 196), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_bg, width=1, border_radius=4)

        active_bg = (84, 112, 84) if well.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(WellPanel.toggle_label(well), True, (240, 242, 250))
        surface.blit(label, (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2))

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        well: Well,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            well,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = WellPanel.layout(
            surface,
            well,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
