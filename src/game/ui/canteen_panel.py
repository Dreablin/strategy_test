"""Canteen panel: cook production, local inputs, active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.canteen import Canteen
from game.resource_catalog import resource_display_label
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 168
_LINE = 22


@dataclass(frozen=True, slots=True)
class CanteenPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class CanteenPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, Canteen)

    @staticmethod
    def toggle_label(canteen: Canteen) -> str:
        return "Active" if canteen.active else "Inactive"

    @staticmethod
    def blocked_reason(
        canteen: Canteen,
        *,
        worker_status: str,
        production_status: str | None,
    ) -> str:
        status = (production_status or "").strip().lower()
        if not canteen.active:
            return "inactive"
        if worker_status == "empty" or status == "no worker":
            return "no worker"
        if status == "resting":
            return "resting"
        if canteen.local_storage_amount("simple_meal") >= canteen.local_storage_capacity("simple_meal"):
            return "output full"
        if canteen.local_storage_amount("chicken") <= 0:
            return "no chicken"
        if canteen.local_storage_amount("bread") <= 0:
            return "no bread"
        if canteen.local_storage_amount("water") <= 0:
            return "no water"
        if status == "processing":
            return "running"
        return "running"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        canteen: Canteen,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> CanteenPanelLayout:
        base = BuildingPanel.layout(
            surface,
            canteen,
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
        return CanteenPanelLayout(
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
        canteen: Canteen,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int,
    ) -> None:
        BuildingPanel.draw(
            surface,
            canteen,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_status == "assigned",
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = CanteenPanel.layout(
            surface,
            canteen,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = pygame.font.Font(None, 22)
        body = pygame.font.Font(None, 20)

        details_y = layout.frame.top + _PANEL_PAD + 4 * 26 + 32
        lines = (
            f"Chicken: {canteen.local_storage_amount('chicken')} / {canteen.local_storage_capacity('chicken')}",
            f"Bread: {canteen.local_storage_amount('bread')} / {canteen.local_storage_capacity('bread')}",
            f"Water: {canteen.local_storage_amount('water')} / {canteen.local_storage_capacity('water')}",
            f"{resource_display_label('simple_meal')}: {canteen.local_storage_amount('simple_meal')} / "
            f"{canteen.local_storage_capacity('simple_meal')}",
        )
        for i, text in enumerate(lines):
            surf = body.render(text, True, (200, 204, 214))
            surface.blit(surf, (layout.frame.left + _PANEL_PAD, details_y + i * _LINE))

        reason = CanteenPanel.blocked_reason(
            canteen,
            worker_status=worker_status,
            production_status=production_status,
        )
        reason_y = details_y + 4 * _LINE
        surface.blit(body.render(f"Blocked: {reason}", True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, reason_y))

        bar_y = reason_y + _LINE
        bar_bg = pygame.Rect(layout.frame.left + _PANEL_PAD, bar_y, layout.frame.width - _PANEL_PAD * 2, 12)
        pygame.draw.rect(surface, (52, 58, 66), bar_bg, border_radius=4)
        progress = max(0.0, min(1.0, canteen.processing_progress(now_ms)))
        if progress > 0.0:
            fill_w = max(1, int(round(bar_bg.width * progress)))
            fill = pygame.Rect(bar_bg.left, bar_bg.top, fill_w, bar_bg.height)
            pygame.draw.rect(surface, (210, 150, 95), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_bg, width=1, border_radius=4)

        active_bg = (84, 112, 84) if canteen.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(CanteenPanel.toggle_label(canteen), True, (240, 242, 250))
        surface.blit(
            label,
            (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        canteen: Canteen,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            canteen,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = CanteenPanel.layout(
            surface,
            canteen,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
