"""School panel with worker hire actions."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets import hire_ui_icon, worker_ui_icon
from game import i18n
from game.ui.building_panel import building_display_name, draw_upgrade_cost_tooltip
from game.ui.fonts import ui_font
from game.ui.worker_labels import (
    building_worker_status_line,
    worker_display_label,
)
from game.buildings.school import SCHOOL_TRAINING_MS, School
from game.worker_tiers import worker_tier
from game.workers import WorkerManager

_PANEL_W = 420
_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8
_QUEUE_SLOT = 30
_SECTION_TITLE_GAP = 24
_TILE_COLS = 3
_TILE_W = 124
_TILE_H = 82
_TILE_GAP = 8
_HIRE_ROWS: tuple[str, ...] = (
    "CARRIER",
    "BUILDER",
    "SAWYER",
    "MILLER",
    "BAKER",
    "COOK",
    "WATERMAN",
    "LUMBERJACK",
    "STONECUTTER",
    "MINER",
    "FARMER",
    "ANIMAL_HERDER",
    "FORESTER",
    "WINEMAKER",
    "SCIENTIST",
)
_TAB_H = 28
_TAB_GAP = 6


def _hire_rows_for_tier(tier: str) -> tuple[str, ...]:
    return tuple(w for w in _HIRE_ROWS if worker_tier(w) == tier)


def _hire_grid_rows_for(count: int) -> int:
    return max(1, (count + _TILE_COLS - 1) // _TILE_COLS)


def _max_hire_grid_rows() -> int:
    tiers = {worker_tier(w) for w in _HIRE_ROWS}
    return max(_hire_grid_rows_for(len(_hire_rows_for_tier(tier))) for tier in tiers)


@dataclass(frozen=True, slots=True)
class SchoolPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect
    queue_slots: tuple[pygame.Rect, ...]
    hire_buttons: tuple[tuple[str, pygame.Rect], ...]
    hire_enabled: dict[str, bool]
    tabs: tuple[tuple[str, pygame.Rect], ...]
    active_tier: str


class SchoolPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, School)

    @staticmethod
    def panel_title(school: School) -> str:
        return i18n.t(
            "ui.school.panel_title",
            name=building_display_name("SCHOOL"),
            level=school.level,
        )

    @staticmethod
    def queue_title() -> str:
        return i18n.t("ui.school.queue")

    @staticmethod
    def tab_label(tier: str) -> str:
        return i18n.t(f"ui.school.tab.{tier}")

    @staticmethod
    def layout(
        surface: pygame.Surface,
        school: School,
        *,
        worker_assigned: bool,
        worker_manager: WorkerManager | None = None,
        tier: str = "basic",
    ) -> SchoolPanelLayout:
        filtered_rows = _hire_rows_for_tier(tier)
        grid_rows = _max_hire_grid_rows()
        grid_h = grid_rows * _TILE_H + (grid_rows - 1) * _TILE_GAP
        sw, sh = surface.get_size()
        tab_section_h = _TAB_H + _TAB_GAP
        content_h = 26 + 34 + _SECTION_TITLE_GAP + _QUEUE_SLOT + _GAP + _BTN_H + 14 + tab_section_h + grid_h
        frame_h = _PANEL_PAD * 2 + content_h
        frame = pygame.Rect(sw // 2 - _PANEL_W // 2, sh // 2 - frame_h // 2, _PANEL_W, frame_h)
        close = pygame.Rect(
            frame.right - _PANEL_PAD - 28,
            frame.top + _PANEL_PAD,
            28,
            28,
        )
        queue_y = frame.top + _PANEL_PAD + 26 + 34 + _SECTION_TITLE_GAP
        queue_slots: list[pygame.Rect] = []
        qx = frame.left + _PANEL_PAD
        for _ in range(7):
            queue_slots.append(pygame.Rect(qx, queue_y, _QUEUE_SLOT, _QUEUE_SLOT))
            qx += _QUEUE_SLOT + _GAP
        action_y = queue_y + _QUEUE_SLOT + _GAP
        action_w = (frame.width - _PANEL_PAD * 2 - _GAP) // 2
        upgrade = None
        upgrade_enabled = school.level < school.max_level() and not school.training_queue()
        if school.level < school.max_level():
            upgrade = pygame.Rect(frame.left + _PANEL_PAD, action_y, action_w, _BTN_H)
        hire_enabled: dict[str, bool] = {}
        demolish_x = frame.left + _PANEL_PAD if upgrade is None else upgrade.right + _GAP
        demolish_w = frame.width - _PANEL_PAD * 2 if upgrade is None else action_w
        demolish = pygame.Rect(demolish_x, action_y, demolish_w, _BTN_H)
        tab_y = action_y + _BTN_H + 14
        tab_w = (frame.width - _PANEL_PAD * 2 - _TAB_GAP) // 2
        tab_basic = pygame.Rect(frame.left + _PANEL_PAD, tab_y, tab_w, _TAB_H)
        tab_advanced = pygame.Rect(tab_basic.right + _TAB_GAP, tab_y, tab_w, _TAB_H)
        tabs: tuple[tuple[str, pygame.Rect], ...] = (("basic", tab_basic), ("advanced", tab_advanced))
        grid_y = tab_y + _TAB_H + _TAB_GAP
        grid_x = frame.left + _PANEL_PAD
        buttons: list[tuple[str, pygame.Rect]] = []
        for idx, worker_type in enumerate(filtered_rows):
            col = idx % _TILE_COLS
            row = idx // _TILE_COLS
            rect = pygame.Rect(
                grid_x + col * (_TILE_W + _TILE_GAP),
                grid_y + row * (_TILE_H + _TILE_GAP),
                _TILE_W,
                _TILE_H,
            )
            buttons.append((worker_type, rect))
            if worker_manager is not None:
                hire_enabled[worker_type] = worker_manager.can_hire(
                    worker_type,
                    charge_cost=False,
                ) and school.can_enqueue_training()
            else:
                hire_enabled[worker_type] = school.can_enqueue_training()
        return SchoolPanelLayout(
            frame=frame,
            close=close,
            upgrade=upgrade,
            upgrade_enabled=upgrade_enabled,
            demolish=demolish,
            queue_slots=tuple(queue_slots),
            hire_buttons=tuple(buttons),
            hire_enabled=hire_enabled,
            tabs=tabs,
            active_tier=tier,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        school: School,
        *,
        worker_assigned: bool,
        worker_manager: WorkerManager | None = None,
        tier: str = "basic",
    ) -> None:
        layout = SchoolPanel.layout(
            surface,
            school,
            worker_assigned=worker_assigned,
            worker_manager=worker_manager,
            tier=tier,
        )
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)
        title_font = ui_font(28)
        font = ui_font(22)
        small_font = ui_font(18)
        title = title_font.render(SchoolPanel.panel_title(school), True, (238, 240, 248))
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
        worker_text = "assigned" if worker_assigned else "empty"
        surface.blit(
            font.render(
                building_worker_status_line(school.type_tag, worker_text),
                True,
                (200, 204, 214),
            ),
            (layout.frame.left + _PANEL_PAD, layout.frame.top + _PANEL_PAD + 52),
        )
        queue_title = font.render(SchoolPanel.queue_title(), True, (220, 228, 236))
        surface.blit(queue_title, (layout.queue_slots[0].left, layout.queue_slots[0].top - _SECTION_TITLE_GAP + 6))
        queue = school.training_queue()
        for idx, slot in enumerate(layout.queue_slots):
            pygame.draw.rect(surface, (52, 58, 66), slot, border_radius=4)
            pygame.draw.rect(surface, (116, 124, 136), slot, width=1, border_radius=4)
            if idx < len(queue):
                icon = worker_ui_icon(queue[idx].type_tag, size=20)
                ix = slot.centerx - icon.get_width() // 2
                iy = slot.centery - icon.get_height() // 2 - 3
                surface.blit(icon, (ix, iy))
            if idx == 0 and queue:
                progress = max(0.0, min(1.0, school.training_progress_ms() / float(SCHOOL_TRAINING_MS)))
                if progress > 0.0:
                    fill_w = max(1, int(round((slot.width - 4) * progress)))
                    bar = pygame.Rect(slot.left + 2, slot.bottom - 5, fill_w, 3)
                    pygame.draw.rect(surface, (230, 210, 64), bar, border_radius=2)
        if layout.upgrade is not None:
            bg = (64, 110, 168) if layout.upgrade_enabled else (52, 56, 64)
            fg = (240, 242, 250) if layout.upgrade_enabled else (130, 134, 142)
            pygame.draw.rect(surface, bg, layout.upgrade, border_radius=6)
            label = font.render(i18n.t("ui.button.upgrade"), True, fg)
            surface.blit(
                label,
                (
                    layout.upgrade.centerx - label.get_width() // 2,
                    layout.upgrade.centery - label.get_height() // 2,
                ),
            )
            draw_upgrade_cost_tooltip(surface, school, layout.upgrade)
        pygame.draw.rect(surface, (140, 48, 52), layout.demolish, border_radius=6)
        d = font.render(i18n.t("ui.button.demolish"), True, (255, 240, 240))
        surface.blit(d, (layout.demolish.centerx - d.get_width() // 2, layout.demolish.centery - d.get_height() // 2))
        for tab_tier, tab_rect in layout.tabs:
            active = tab_tier == layout.active_tier
            tab_bg = (64, 110, 168) if active else (52, 56, 64)
            tab_fg = (240, 242, 250) if active else (160, 164, 174)
            pygame.draw.rect(surface, tab_bg, tab_rect, border_radius=5)
            tab_text = font.render(SchoolPanel.tab_label(tab_tier), True, tab_fg)
            surface.blit(tab_text, (tab_rect.centerx - tab_text.get_width() // 2, tab_rect.centery - tab_text.get_height() // 2))
        for worker_type, rect in layout.hire_buttons:
            enabled = layout.hire_enabled.get(worker_type, False)
            bg = (84, 112, 84) if enabled else (56, 60, 66)
            fg = (236, 244, 236) if enabled else (134, 138, 146)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, (86, 94, 106), rect, width=1, border_radius=6)
            worker_icon = worker_ui_icon(worker_type, size=34)
            hire_icon = hire_ui_icon(worker_type, size=18)
            icon_x = rect.centerx - worker_icon.get_width() // 2
            icon_y = rect.top + 10
            surface.blit(worker_icon, (icon_x, icon_y))
            hire_x = rect.right - hire_icon.get_width() - 8
            hire_y = rect.top + 8
            surface.blit(hire_icon, (hire_x, hire_y))
            label = worker_display_label(worker_type)
            label_text = small_font.render(label, True, fg)
            label_x = rect.centerx - label_text.get_width() // 2
            surface.blit(label_text, (label_x, rect.bottom - label_text.get_height() - 8))

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        school: School,
        *,
        worker_assigned: bool,
        worker_manager: WorkerManager | None = None,
        tier: str = "basic",
    ) -> str | None:
        layout = SchoolPanel.layout(
            surface,
            school,
            worker_assigned=worker_assigned,
            worker_manager=worker_manager,
            tier=tier,
        )
        if layout.close.collidepoint(pos):
            return "close"
        for tab_tier, tab_rect in layout.tabs:
            if tab_rect.collidepoint(pos):
                return f"tab:{tab_tier}"
        if layout.upgrade is not None and layout.upgrade.collidepoint(pos):
            return "upgrade" if layout.upgrade_enabled else None
        if layout.demolish.collidepoint(pos):
            return "demolish"
        queue = school.training_queue()
        for idx, rect in enumerate(layout.queue_slots):
            if idx < len(queue) and rect.collidepoint(pos):
                return f"cancel:{idx}"
        for worker_type, rect in layout.hire_buttons:
            if rect.collidepoint(pos) and layout.hire_enabled.get(worker_type, False):
                return f"hire:{worker_type}"
        return None
