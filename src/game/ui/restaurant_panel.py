"""Restaurant panel with storage rows, progress bar, diner tiles, and active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.restaurant import Restaurant
from game.ui.building_panel import BuildingPanel
from game.worker_dining import dining_eat_duration_ms
from game.worker_status import production_status_for_building


_PANEL_PAD = 16
_BTN_H = 32
_ROW_H = 22
_BAR_H = 12
_DINER_TILE_W = 36
_DINER_TILE_H = 44
_DINER_GAP = 6
_DINER_ROW_GAP = 4
_DINER_ROWS_H = (_DINER_TILE_H + _DINER_ROW_GAP) * 2
_EXTRA_BOTTOM = _ROW_H * 5 + _BAR_H + 24 + _DINER_ROWS_H + 8 + _BTN_H + 8


@dataclass(frozen=True, slots=True)
class RestaurantPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class RestaurantPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, Restaurant)

    @staticmethod
    def toggle_label(restaurant: Restaurant) -> str:
        return "Active" if restaurant.active else "Inactive"

    @staticmethod
    def storage_lines(restaurant: Restaurant) -> dict[str, str]:
        cap = restaurant.local_storage_capacity("bread")
        return {
            "bread": f"Bread: {restaurant.local_storage_amount('bread')} / {cap}",
            "wine": f"Wine: {restaurant.local_storage_amount('wine')} / {cap}",
            "beef": f"Beef: {restaurant.local_storage_amount('beef')} / {cap}",
            "elite_meal": f"Elite meal: {restaurant.output_amount()} / {restaurant.output_capacity()}",
        }

    @staticmethod
    def layout(
        surface: pygame.Surface,
        restaurant: Restaurant,
        *,
        worker_assigned: bool,
    ) -> RestaurantPanelLayout:
        base = BuildingPanel.layout(surface, restaurant, worker_assigned=worker_assigned, extra_bottom_px=_EXTRA_BOTTOM)
        toggle_rect = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - _BTN_H,
            base.frame.width - 2 * _PANEL_PAD,
            _BTN_H,
        )
        return RestaurantPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=base.upgrade,
            upgrade_enabled=base.upgrade_enabled,
            demolish=base.demolish,
            toggle=toggle_rect,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        restaurant: Restaurant,
        *,
        worker_assigned: bool,
        now_ms: int = 0,
        worker_manager=None,
    ) -> RestaurantPanelLayout:
        lay = RestaurantPanel.layout(surface, restaurant, worker_assigned=worker_assigned)
        BuildingPanel.draw(surface, restaurant, worker_assigned=worker_assigned, extra_bottom_px=_EXTRA_BOTTOM)
        font = pygame.font.SysFont(None, 18)

        action_tops = [lay.toggle.top]
        if lay.upgrade is not None:
            action_tops.append(lay.upgrade.top)
        if lay.demolish is not None:
            action_tops.append(lay.demolish.top)
        details_bottom = min(action_tops) - 8
        y = details_bottom - (_ROW_H * 5 + _BAR_H + 4)

        lines = RestaurantPanel.storage_lines(restaurant)
        for key in ("bread", "wine", "beef", "elite_meal"):
            text = font.render(lines[key], True, (220, 222, 230))
            surface.blit(text, (lay.frame.left + _PANEL_PAD, y))
            y += _ROW_H

        status = ""
        if worker_manager is not None:
            status = production_status_for_building(worker_manager, restaurant)
        status_text = font.render(f"Status: {status}", True, (200, 200, 210))
        surface.blit(status_text, (lay.frame.left + _PANEL_PAD, y))
        y += _ROW_H

        bar_rect = pygame.Rect(lay.frame.left + _PANEL_PAD, y, lay.frame.width - 2 * _PANEL_PAD, _BAR_H)
        pygame.draw.rect(surface, (40, 40, 50), bar_rect, border_radius=3)
        progress = restaurant.processing_progress(now_ms)
        if progress > 0:
            fill_w = max(1, int(bar_rect.width * progress))
            fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_w, bar_rect.height)
            pygame.draw.rect(surface, (100, 180, 100), fill_rect, border_radius=3)

        y += _BAR_H + 8
        RestaurantPanel._draw_diner_tiles(surface, restaurant, lay, y, now_ms)

        label = RestaurantPanel.toggle_label(restaurant)
        color = (80, 180, 80) if restaurant.active else (180, 80, 80)
        pygame.draw.rect(surface, color, lay.toggle, border_radius=4)
        btn_font = pygame.font.SysFont(None, 20)
        btn_text = btn_font.render(label, True, (255, 255, 255))
        surface.blit(btn_text, (lay.toggle.centerx - btn_text.get_width() // 2, lay.toggle.centery - btn_text.get_height() // 2))
        return lay

    @staticmethod
    def _draw_diner_tiles(
        surface: pygame.Surface,
        restaurant: Restaurant,
        lay: RestaurantPanelLayout,
        y_start: int,
        now_ms: int,
    ) -> None:
        from game.assets import worker_ui_icon

        slots = restaurant.diner_slot_capacity()
        if slots <= 0:
            return
        width = lay.frame.width - _PANEL_PAD * 2
        cols = max(1, (width + _DINER_GAP) // (_DINER_TILE_W + _DINER_GAP))
        left = lay.frame.left + _PANEL_PAD
        occupants = sorted(restaurant._diner_occupants, key=id)
        for idx in range(slots):
            row = idx // cols
            col = idx % cols
            x = left + col * (_DINER_TILE_W + _DINER_GAP)
            y = y_start + row * (_DINER_TILE_H + _DINER_ROW_GAP)
            tile = pygame.Rect(x, y, _DINER_TILE_W, _DINER_TILE_H)
            occupied = idx < len(occupants)
            bg = (74, 84, 96) if occupied else (52, 58, 66)
            pygame.draw.rect(surface, bg, tile, border_radius=4)
            pygame.draw.rect(surface, (116, 124, 136), tile, width=1, border_radius=4)
            if not occupied:
                continue
            diner = occupants[idx]
            phase = str(getattr(diner, "dining_phase", "none"))
            icon = worker_ui_icon(diner.type_tag, size=20)
            if phase not in {"waiting_for_meal", "eating"}:
                icon = icon.copy()
                icon.set_alpha(128)
            icon_pos = (
                tile.left + (tile.width - icon.get_width()) // 2,
                tile.top + 4,
            )
            surface.blit(icon, icon_pos)
            if phase == "eating":
                started = int(getattr(diner, "dining_eating_started_ms", 0))
                t = 0.0 if started <= 0 else max(
                    0.0,
                    min(1.0, (int(now_ms) - started) / float(dining_eat_duration_ms(restaurant))),
                )
                progress_bg = pygame.Rect(tile.left, tile.bottom - 4, tile.width, 3)
                pygame.draw.rect(surface, (44, 48, 56), progress_bg, border_radius=2)
                if t > 0:
                    pw = max(1, int(progress_bg.width * t))
                    pygame.draw.rect(
                        surface,
                        (100, 200, 100),
                        pygame.Rect(progress_bg.left, progress_bg.top, pw, progress_bg.height),
                        border_radius=2,
                    )

    @staticmethod
    def diner_visual_state(restaurant: Restaurant, diner_index: int) -> str:
        """Return 'empty', 'walking', 'waiting', or 'eating' for a given diner slot."""
        occupants = sorted(restaurant._diner_occupants, key=id)
        if diner_index >= len(occupants):
            return "empty"
        diner = occupants[diner_index]
        phase = str(getattr(diner, "dining_phase", "none"))
        if phase == "eating":
            return "eating"
        if phase in {"waiting_for_meal"}:
            return "waiting"
        return "walking"

    @staticmethod
    def click_action(
        pos: tuple[int, int],
        layout: RestaurantPanelLayout,
    ) -> str | None:
        x, y = pos
        if layout.close.collidepoint(x, y):
            return "close"
        if layout.upgrade is not None and layout.upgrade.collidepoint(x, y):
            return "upgrade"
        if layout.demolish is not None and layout.demolish.collidepoint(x, y):
            return "demolish"
        if layout.toggle.collidepoint(x, y):
            return "toggle_active"
        return None
