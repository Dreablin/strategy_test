"""Vineyard Farm panel: grape storage row, worker/status via BuildingPanel, actions, toggle (T333–T334)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.vineyard_farm import VineyardFarm
from game.ui.building_panel import BuildingPanel
from game.ui.fonts import ui_font

_PANEL_PAD = 16
_BTN_H = 32
_ROW = 26
# Reserve space for grape row + gap + toggle; phantom button slot at max level keeps buttons clear of toggle.
_EXTRA_BOTTOM = 104


@dataclass(frozen=True, slots=True)
class VineyardFarmPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class VineyardFarmPanel:
    @staticmethod
    def supports_building(building: object) -> bool:
        return isinstance(building, VineyardFarm)

    @staticmethod
    def grape_storage_line(farm: VineyardFarm) -> str:
        return f"Grapes: {farm.grapes_amount()} / {farm.grapes_capacity()}"

    @staticmethod
    def _grape_label_y(layout: VineyardFarmPanelLayout) -> int:
        """Place the grape line in the gap above the topmost primary action (upgrade or demolish)."""
        if layout.upgrade is not None:
            anchor_top = layout.upgrade.top
        elif layout.demolish is not None:
            anchor_top = layout.demolish.top
        else:
            anchor_top = layout.toggle.top
        return anchor_top - _ROW - 8

    @staticmethod
    def toggle_label(farm: VineyardFarm) -> str:
        return "Active" if farm.active else "Inactive"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        farm: VineyardFarm,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> VineyardFarmPanelLayout:
        base = BuildingPanel.layout(
            surface,
            farm,
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
        return VineyardFarmPanelLayout(
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
        farm: VineyardFarm,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int = 0,
    ) -> None:
        _ = now_ms
        BuildingPanel.draw(
            surface,
            farm,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_status == "assigned",
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = VineyardFarmPanel.layout(
            surface,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        body_font = ui_font(22)
        grape_y = VineyardFarmPanel._grape_label_y(layout)
        surface.blit(
            body_font.render(VineyardFarmPanel.grape_storage_line(farm), True, (200, 204, 214)),
            (layout.frame.left + _PANEL_PAD, grape_y),
        )
        font = ui_font(22)
        active_bg = (84, 112, 84) if farm.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(VineyardFarmPanel.toggle_label(farm), True, (240, 242, 250))
        surface.blit(
            label,
            (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        farm: VineyardFarm,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = VineyardFarmPanel.layout(
            surface,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
