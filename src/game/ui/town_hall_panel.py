"""Town Hall modal extension: no upgrade/demolish, with hire buttons (PRD F-UI-PANEL-03)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets import hire_ui_icon, resource_icon, worker_ui_icon
from game.buildings.costs import upgrade_cost
from game.buildings.town_hall import TownHall
from game.config import TOWN_HALL_MIN_LEVEL_FOR_HIRE, WORKER_HIRE_COSTS
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8
_SECTION_TITLE_GAP = 24
_EXTRA_BOTTOM = _SECTION_TITLE_GAP + (_BTN_H + _GAP) * len(
    (
        "LUMBERJACK",
        "STONECUTTER",
        "MINER",
        "FARMER",
    )
)
_WORKER_ICON_SIZE = 22
_HIRE_ICON_SIZE = 18
_FOOD_ICON_SIZE = 16

_HIRE_ROWS: tuple[str, ...] = ("LUMBERJACK", "STONECUTTER", "MINER", "FARMER")
_WORKER_LABEL: dict[str, str] = {
    "LUMBERJACK": "Lumberjack",
    "STONECUTTER": "Stonecutter",
    "MINER": "Miner",
    "FARMER": "Farmer",
}


@dataclass(frozen=True, slots=True)
class TownHallPanelLayout:
    """Town Hall panel frame and hire button rects."""

    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    hire_buttons: tuple[tuple[str, pygame.Rect], ...]
    hire_enabled: dict[str, bool]


class TownHallPanel:
    @staticmethod
    def _format_cost(cost: dict[str, int]) -> str:
        parts: list[str] = []
        for key in ("wood", "stone", "iron", "food"):
            value = int(cost.get(key, 0))
            if value > 0:
                parts.append(f"{value} {key}")
        return ", ".join(parts) if parts else "—"

    """Town Hall panel: base info rows + hire worker section."""

    @staticmethod
    def layout(
        surface: pygame.Surface, town_hall: TownHall, resources: ResourceManager, *, worker_assigned: bool
    ) -> TownHallPanelLayout:
        base = BuildingPanel.layout(
            surface,
            town_hall,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        upgrade: pygame.Rect | None = None
        upgrade_enabled = False
        if town_hall.level < TownHall.max_level():
            try:
                up_cost = upgrade_cost(town_hall.level)
            except ValueError:
                up_cost = {}
            else:
                upgrade_enabled = resources.has(up_cost)
            upgrade = pygame.Rect(
                base.frame.left + _PANEL_PAD,
                base.frame.bottom - _PANEL_PAD - (_BTN_H + _GAP) * len(_HIRE_ROWS) - (_BTN_H + 8),
                base.frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )

        hire_enabled: dict[str, bool] = {}
        y = base.frame.bottom - _PANEL_PAD - (_BTN_H + _GAP) * len(_HIRE_ROWS)
        buttons: list[tuple[str, pygame.Rect]] = []
        for worker_type in _HIRE_ROWS:
            rect = pygame.Rect(base.frame.left + _PANEL_PAD, y, base.frame.width - _PANEL_PAD * 2, _BTN_H)
            buttons.append((worker_type, rect))
            cost = dict(WORKER_HIRE_COSTS.get(worker_type, {"food": 0}))
            required_lv = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
            hire_enabled[worker_type] = resources.has(cost) and town_hall.level >= required_lv
            y += _BTN_H + _GAP
        return TownHallPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=upgrade,
            upgrade_enabled=upgrade_enabled,
            hire_buttons=tuple(buttons),
            hire_enabled=hire_enabled,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface, town_hall: TownHall, resources: ResourceManager, *, worker_assigned: bool
    ) -> None:
        BuildingPanel.draw(
            surface,
            town_hall,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=worker_assigned)
        font = pygame.font.Font(None, 22)
        title = font.render("Hire Workers", True, (224, 228, 236))
        section_y = layout.hire_buttons[0][1].top - _SECTION_TITLE_GAP
        surface.blit(title, (layout.frame.left + _PANEL_PAD, section_y))

        if layout.upgrade is not None:
            bg = (64, 110, 168) if layout.upgrade_enabled else (52, 56, 64)
            fg = (240, 242, 250) if layout.upgrade_enabled else (130, 134, 142)
            pygame.draw.rect(surface, bg, layout.upgrade, border_radius=6)
            cost = upgrade_cost(town_hall.level)
            text = font.render(f"Upgrade Town Hall — {TownHallPanel._format_cost(cost)}", True, fg)
            surface.blit(
                text,
                (layout.upgrade.centerx - text.get_width() // 2, layout.upgrade.centery - text.get_height() // 2),
            )

        for worker_type, rect in layout.hire_buttons:
            enabled = layout.hire_enabled.get(worker_type, False)
            bg = (84, 112, 84) if enabled else (56, 60, 66)
            fg = (236, 244, 236) if enabled else (134, 138, 146)
            pygame.draw.rect(surface, bg, rect, border_radius=6)

            # Icon-first hire row: worker icon + hire icon + numeric food cost.
            worker_icon = worker_ui_icon(worker_type, size=_WORKER_ICON_SIZE)
            hire_icon = hire_ui_icon(worker_type, size=_HIRE_ICON_SIZE)
            food_icon = pygame.transform.smoothscale(resource_icon("food"), (_FOOD_ICON_SIZE, _FOOD_ICON_SIZE))
            cost_food = int(WORKER_HIRE_COSTS.get(worker_type, {}).get("food", 0))
            cost_text = font.render(str(cost_food), True, fg)

            lx = rect.left + 10
            ly = rect.centery - worker_icon.get_height() // 2
            surface.blit(worker_icon, (lx, ly))

            rx = rect.right - 10
            fy = rect.centery - food_icon.get_height() // 2
            rx -= food_icon.get_width()
            surface.blit(food_icon, (rx, fy))
            rx -= 4 + cost_text.get_width()
            surface.blit(cost_text, (rx, rect.centery - cost_text.get_height() // 2))
            rx -= 8 + hire_icon.get_width()
            surface.blit(hire_icon, (rx, rect.centery - hire_icon.get_height() // 2))

            # Worker label in the middle between left and right icon groups.
            label = _WORKER_LABEL.get(worker_type, worker_type.title())
            label_text = font.render(label, True, fg)
            label_left = lx + worker_icon.get_width() + 10
            label_right = rx - 8
            if label_right > label_left:
                label_x = label_left + max(0, (label_right - label_left - label_text.get_width()) // 2)
                surface.blit(label_text, (label_x, rect.centery - label_text.get_height() // 2))

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        town_hall: TownHall,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
    ) -> str | None:
        """Return ``close`` or ``hire:<WORKER_TYPE>`` when active, else ``None``."""
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            town_hall,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action == "close":
            return "close"
        layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=worker_assigned)
        if layout.upgrade is not None and layout.upgrade.collidepoint(pos):
            return "upgrade" if layout.upgrade_enabled else None
        for worker_type, rect in layout.hire_buttons:
            if rect.collidepoint(pos) and layout.hire_enabled.get(worker_type, False):
                return f"hire:{worker_type}"
        return None
