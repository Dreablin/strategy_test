"""Sawmill panel with active toggle and production details."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.sawmill import Sawmill
from game.ui.building_panel import BuildingPanel
from game.ui.panel_i18n import active_toggle_label, blocked_line, flow_line
from game.ui.fonts import ui_font

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 128


@dataclass(frozen=True, slots=True)
class SawmillPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class SawmillPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, Sawmill)

    @staticmethod
    def toggle_label(sawmill: Sawmill) -> str:
        return active_toggle_label(sawmill.active)

    @staticmethod
    def blocked_reason(
        sawmill: Sawmill, *, worker_status: str, production_status: str | None
    ) -> str:
        status = (production_status or "").strip()
        if not sawmill.active:
            return "inactive"
        if worker_status == "empty" or status == "no_worker":
            return "no worker"
        if status == "resting":
            return "resting"
        if sawmill.output_amount() >= sawmill.output_capacity():
            return "output full"
        if sawmill.input_amount() <= 0:
            return "no wood"
        return "running"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        sawmill: Sawmill,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> SawmillPanelLayout:
        base = BuildingPanel.layout(
            surface,
            sawmill,
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
        return SawmillPanelLayout(
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
        sawmill: Sawmill,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int,
    ) -> None:
        BuildingPanel.draw(
            surface,
            sawmill,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_status == "assigned",
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = SawmillPanel.layout(
            surface,
            sawmill,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = ui_font(22)
        body = ui_font(20)

        details_y = layout.frame.top + _PANEL_PAD + 4 * 26 + 32
        io = body.render(
            flow_line(
                role_key="ui.panel.input",
                resource_key="wood",
                amount=sawmill.input_amount(),
                capacity=sawmill.input_capacity(),
            ),
            True,
            (200, 204, 214),
        )
        surface.blit(io, (layout.frame.left + _PANEL_PAD, details_y))
        out = body.render(
            flow_line(
                role_key="ui.panel.output",
                resource_key="boards",
                amount=sawmill.output_amount(),
                capacity=sawmill.output_capacity(),
            ),
            True,
            (200, 204, 214),
        )
        surface.blit(out, (layout.frame.left + _PANEL_PAD, details_y + 22))
        reason = SawmillPanel.blocked_reason(
            sawmill, worker_status=worker_status, production_status=production_status
        )
        reason_text = body.render(blocked_line(reason), True, (200, 204, 214))
        surface.blit(reason_text, (layout.frame.left + _PANEL_PAD, details_y + 44))

        bar_y = details_y + 68
        bar_bg = pygame.Rect(layout.frame.left + _PANEL_PAD, bar_y, layout.frame.width - _PANEL_PAD * 2, 12)
        pygame.draw.rect(surface, (52, 58, 66), bar_bg, border_radius=4)
        progress = max(0.0, min(1.0, sawmill.processing_progress(now_ms)))
        if progress > 0.0:
            fill = pygame.Rect(bar_bg.left, bar_bg.top, max(1, int(round(bar_bg.width * progress))), bar_bg.height)
            pygame.draw.rect(surface, (230, 210, 64), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_bg, width=1, border_radius=4)

        active_bg = (84, 112, 84) if sawmill.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(SawmillPanel.toggle_label(sawmill), True, (240, 242, 250))
        surface.blit(label, (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2))

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        sawmill: Sawmill,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            sawmill,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = SawmillPanel.layout(
            surface,
            sawmill,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
