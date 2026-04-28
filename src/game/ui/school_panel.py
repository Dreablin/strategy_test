"""School panel with worker hire actions."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets import hire_ui_icon, resource_icon, worker_ui_icon
from game.buildings.school import School
from game.config import WORKER_HIRE_COSTS
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel
from game.workers import WorkerManager

_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8
_SECTION_TITLE_GAP = 24
_HIRE_ROWS: tuple[str, ...] = ("LUMBERJACK", "STONECUTTER", "MINER", "FARMER", "FORESTER")
_WORKER_LABEL: dict[str, str] = {
    "LUMBERJACK": "Lumberjack",
    "STONECUTTER": "Stonecutter",
    "MINER": "Miner",
    "FARMER": "Farmer",
    "FORESTER": "Forester",
}
_EXTRA_BOTTOM = _SECTION_TITLE_GAP + (_BTN_H + _GAP) * len(_HIRE_ROWS) + (_BTN_H + _GAP)


@dataclass(frozen=True, slots=True)
class SchoolPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    demolish: pygame.Rect
    hire_buttons: tuple[tuple[str, pygame.Rect], ...]
    hire_enabled: dict[str, bool]


class SchoolPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, School)

    @staticmethod
    def layout(
        surface: pygame.Surface,
        school: School,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_manager: WorkerManager | None = None,
    ) -> SchoolPanelLayout:
        base = BuildingPanel.layout(
            surface,
            school,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        demolish = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - (_BTN_H + _GAP) - (_BTN_H + _GAP) * len(_HIRE_ROWS),
            base.frame.width - _PANEL_PAD * 2,
            _BTN_H,
        )
        hire_enabled: dict[str, bool] = {}
        y = demolish.bottom + _GAP
        buttons: list[tuple[str, pygame.Rect]] = []
        for worker_type in _HIRE_ROWS:
            rect = pygame.Rect(base.frame.left + _PANEL_PAD, y, base.frame.width - _PANEL_PAD * 2, _BTN_H)
            buttons.append((worker_type, rect))
            if worker_manager is not None:
                hire_enabled[worker_type] = worker_manager.can_hire(worker_type)
            else:
                cost = dict(WORKER_HIRE_COSTS.get(worker_type, {"food": 0}))
                hire_enabled[worker_type] = resources.has(cost)
            y += _BTN_H + _GAP
        return SchoolPanelLayout(
            frame=base.frame,
            close=base.close,
            demolish=demolish,
            hire_buttons=tuple(buttons),
            hire_enabled=hire_enabled,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        school: School,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_manager: WorkerManager | None = None,
    ) -> None:
        BuildingPanel.draw(
            surface,
            school,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = SchoolPanel.layout(
            surface,
            school,
            resources,
            worker_assigned=worker_assigned,
            worker_manager=worker_manager,
        )
        font = pygame.font.Font(None, 22)
        pygame.draw.rect(surface, (140, 48, 52), layout.demolish, border_radius=6)
        d = font.render("Demolish", True, (255, 240, 240))
        surface.blit(d, (layout.demolish.centerx - d.get_width() // 2, layout.demolish.centery - d.get_height() // 2))
        for worker_type, rect in layout.hire_buttons:
            enabled = layout.hire_enabled.get(worker_type, False)
            bg = (84, 112, 84) if enabled else (56, 60, 66)
            fg = (236, 244, 236) if enabled else (134, 138, 146)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            worker_icon = worker_ui_icon(worker_type, size=22)
            hire_icon = hire_ui_icon(worker_type, size=18)
            food_icon = pygame.transform.smoothscale(resource_icon("food"), (16, 16))
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
        school: School,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_manager: WorkerManager | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            school,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = SchoolPanel.layout(
            surface,
            school,
            resources,
            worker_assigned=worker_assigned,
            worker_manager=worker_manager,
        )
        if layout.demolish.collidepoint(pos):
            return "demolish"
        for worker_type, rect in layout.hire_buttons:
            if rect.collidepoint(pos) and layout.hire_enabled.get(worker_type, False):
                return f"hire:{worker_type}"
        return None
