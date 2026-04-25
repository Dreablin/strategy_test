"""Town Hall modal extension: no upgrade/demolish, with hire buttons (PRD F-UI-PANEL-03)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.town_hall import TownHall
from game.config import WORKER_HIRE_COST
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8

_HIRE_ROWS: tuple[tuple[str, str], ...] = (
    ("LUMBERJACK", "Hire Lumberjack"),
    ("STONECUTTER", "Hire Stonecutter"),
    ("MINER", "Hire Miner"),
    ("FARMER", "Hire Farmer"),
)


@dataclass(frozen=True, slots=True)
class TownHallPanelLayout:
    """Town Hall panel frame and hire button rects."""

    frame: pygame.Rect
    close: pygame.Rect
    hire_buttons: tuple[tuple[str, pygame.Rect], ...]
    hire_enabled: bool


class TownHallPanel:
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
        )
        hire_enabled = resources.has(WORKER_HIRE_COST)
        y = base.frame.bottom - _PANEL_PAD - (_BTN_H + _GAP) * len(_HIRE_ROWS)
        buttons: list[tuple[str, pygame.Rect]] = []
        for worker_type, _ in _HIRE_ROWS:
            rect = pygame.Rect(base.frame.left + _PANEL_PAD, y, base.frame.width - _PANEL_PAD * 2, _BTN_H)
            buttons.append((worker_type, rect))
            y += _BTN_H + _GAP
        return TownHallPanelLayout(
            frame=base.frame, close=base.close, hire_buttons=tuple(buttons), hire_enabled=hire_enabled
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
        )
        layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=worker_assigned)
        font = pygame.font.Font(None, 22)
        title = font.render("Hire Workers", True, (224, 228, 236))
        section_y = layout.hire_buttons[0][1].top - 24
        surface.blit(title, (layout.frame.left + _PANEL_PAD, section_y))

        for worker_type, rect in layout.hire_buttons:
            label = next(lbl for key, lbl in _HIRE_ROWS if key == worker_type)
            bg = (84, 112, 84) if layout.hire_enabled else (56, 60, 66)
            fg = (236, 244, 236) if layout.hire_enabled else (134, 138, 146)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            text = font.render(f"{label} — 50 food", True, fg)
            surface.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

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
        )
        if base_action == "close":
            return "close"
        layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=worker_assigned)
        if not layout.hire_enabled:
            return None
        for worker_type, rect in layout.hire_buttons:
            if rect.collidepoint(pos):
                return f"hire:{worker_type}"
        return None
