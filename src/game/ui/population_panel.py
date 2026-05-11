"""Scrollable population panel with worker summaries."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets import worker_ui_icon
from game.worker_models import Worker

_PANEL_W = 560
_PANEL_PAD = 16
_HEADER_H = 32
_FILTER_H = 40
_FILTER_GAP = 5
_FILTER_TILE = 34
_ROW_H = 72
_ROW_GAP = 8
_CLOSE = 28
_FILTER_WORKER_TYPES: tuple[str, ...] = (
    "CARRIER",
    "BUILDER",
    "SAWYER",
    "MILLER",
    "BAKER",
    "LUMBERJACK",
    "STONECUTTER",
    "MINER",
    "FARMER",
    "ANIMAL_HERDER",
    "FORESTER",
    "COOK",
    "WATERMAN",
)

_WORKER_LABEL: dict[str, str] = {
    "CARRIER": "Carrier",
    "BUILDER": "Builder",
    "SAWYER": "Sawyer",
    "MILLER": "Miller",
    "BAKER": "Baker",
    "LUMBERJACK": "Lumberjack",
    "STONECUTTER": "Stonecutter",
    "MINER": "Miner",
    "FARMER": "Farmer",
    "ANIMAL_HERDER": "Herder",
    "FORESTER": "Forester",
    "COOK": "Cook",
    "WATERMAN": "Waterman",
}

_BUILDING_LABEL: dict[str, str] = {
    "TOWN_HALL": "Town Hall",
    "LUMBER_CAMP": "Lumber Camp",
    "STONE_MINE": "Stone Mine",
    "IRON_MINE": "Iron Mine",
    "FARM": "Farm",
    "FORESTER_HUT": "Forester Hut",
    "SAWMILL": "Sawmill",
    "MILL": "Mill",
    "BAKERY": "Bakery",
    "CHICKEN_FARM": "Chicken Farm",
    "COW_FARM": "Cow Farm",
    "SCHOOL": "School",
    "WELL": "Well",
    "CANTEEN": "Canteen",
}

_RESOURCE_LABEL: dict[str, str] = {
    "wood": "wood",
    "stone": "stone",
    "iron": "iron",
    "boards": "boards",
    "wheat": "wheat",
    "flour": "flour",
    "bread": "bread",
    "chicken": "chicken",
    "beef": "beef",
    "hide": "hide",
    "grapes": "grapes",
    "water": "water",
}

_STATE_LABEL: dict[str, str] = {
    "idle": "Idle",
    "working": "Working",
    "resting": "Resting",
    "moving": "Moving",
    "building": "Building",
    "going_to_tree": "Going to tree",
    "going_to_stone": "Going to stone",
    "going_to_plant_tile": "Going to plant",
    "going_to_field": "Going to field",
    "returning": "Returning",
    "sowing": "Sowing",
    "harvesting": "Harvesting",
    "going_to_canteen": "Going to canteen",
    "waiting_for_meal": "Waiting for meal",
    "eating": "Eating",
    "carrier_moving_to_source": "Going to pickup",
    "carrier_loading": "Loading",
    "carrier_unloading": "Unloading",
}


@dataclass(frozen=True, slots=True)
class PopulationPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    filters: tuple[tuple[str | None, pygame.Rect], ...]
    content: pygame.Rect
    max_scroll: int


def _label(value: str | None, labels: dict[str, str]) -> str:
    if value is None:
        return "none"
    return labels.get(value, value.replace("_", " ").title())


def _building_name(building) -> str:
    if building is None:
        return "none"
    return _label(str(getattr(building, "type_tag", "")), _BUILDING_LABEL)


def worker_summary(worker: Worker) -> tuple[str, str, str]:
    """Return title, task line, detail line for a population row."""
    title = _label(worker.type_tag, _WORKER_LABEL)
    task = worker.transport_task
    if task is not None:
        resource = _label(task.resource, _RESOURCE_LABEL)
        action = "Returning" if task.returning_to_town_hall else "Carrying" if worker.carrying else "Fetching"
        task_line = f"{action} {resource}"
        detail = f"{_building_name(task.source)} -> {_building_name(task.target)}"
        return title, task_line, detail

    state = _label(worker.state, _STATE_LABEL)
    assigned = _building_name(worker.assigned_building)
    carrying = _label(worker.carrying, _RESOURCE_LABEL)
    task_line = state
    detail = f"Assigned: {assigned}"
    if worker.carrying is not None:
        detail = f"{detail} | Carrying: {carrying}"
    return title, task_line, detail


def _filtered_workers(workers: tuple[Worker, ...], worker_filter: str | None) -> tuple[Worker, ...]:
    if worker_filter is None:
        return workers
    return tuple(worker for worker in workers if worker.type_tag == worker_filter)


class PopulationPanel:
    """Read-only scrollable list of all workers."""

    @staticmethod
    def layout(
        surface: pygame.Surface,
        workers: tuple[Worker, ...],
        scroll_y: int = 0,
        worker_filter: str | None = None,
    ) -> PopulationPanelLayout:
        sw, sh = surface.get_size()
        frame_h = min(560, max(260, sh - 120))
        frame = pygame.Rect(sw // 2 - _PANEL_W // 2, sh // 2 - frame_h // 2, _PANEL_W, frame_h)
        close = pygame.Rect(frame.right - _PANEL_PAD - _CLOSE, frame.top + _PANEL_PAD, _CLOSE, _CLOSE)
        filter_y = frame.top + _PANEL_PAD + _HEADER_H + 8
        filters: list[tuple[str | None, pygame.Rect]] = []
        fx = frame.left + _PANEL_PAD
        filters.append((None, pygame.Rect(fx, filter_y, 58, _FILTER_H)))
        fx += 58 + _FILTER_GAP
        for worker_type in _FILTER_WORKER_TYPES:
            filters.append((worker_type, pygame.Rect(fx, filter_y, _FILTER_TILE, _FILTER_H)))
            fx += _FILTER_TILE + _FILTER_GAP
        content = pygame.Rect(
            frame.left + _PANEL_PAD,
            filter_y + _FILTER_H + 12,
            frame.width - _PANEL_PAD * 2,
            frame.bottom - _PANEL_PAD - (filter_y + _FILTER_H + 12),
        )
        visible_workers = _filtered_workers(workers, worker_filter)
        content_h = len(visible_workers) * _ROW_H + max(0, len(visible_workers) - 1) * _ROW_GAP
        _ = scroll_y
        return PopulationPanelLayout(frame, close, tuple(filters), content, max(0, content_h - content.height))

    @staticmethod
    def clamp_scroll(
        surface: pygame.Surface,
        workers: tuple[Worker, ...],
        scroll_y: int,
        worker_filter: str | None = None,
    ) -> int:
        layout = PopulationPanel.layout(surface, workers, scroll_y, worker_filter)
        return max(0, min(int(scroll_y), layout.max_scroll))

    @staticmethod
    def draw(
        surface: pygame.Surface,
        workers: tuple[Worker, ...],
        scroll_y: int = 0,
        worker_filter: str | None = None,
    ) -> None:
        layout = PopulationPanel.layout(surface, workers, scroll_y, worker_filter)
        scroll_y = PopulationPanel.clamp_scroll(surface, workers, scroll_y, worker_filter)
        visible_workers = _filtered_workers(workers, worker_filter)

        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)

        title_font = pygame.font.Font(None, 28)
        body_font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 20)
        title = title_font.render(f"Population - {len(workers)}", True, (238, 240, 248))
        surface.blit(title, (layout.frame.left + _PANEL_PAD, layout.frame.top + _PANEL_PAD))

        pygame.draw.line(surface, (200, 82, 82), (layout.close.left + 6, layout.close.top + 6), (layout.close.right - 7, layout.close.bottom - 7), 2)
        pygame.draw.line(surface, (200, 82, 82), (layout.close.right - 7, layout.close.top + 6), (layout.close.left + 6, layout.close.bottom - 7), 2)

        for worker_type, rect in layout.filters:
            selected = worker_type == worker_filter
            bg = (76, 104, 76) if selected else (48, 54, 66)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, (92, 102, 120), rect, width=1, border_radius=6)
            if worker_type is None:
                text = small_font.render("All", True, (238, 240, 248))
                surface.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
            else:
                icon = worker_ui_icon(worker_type, size=26)
                surface.blit(icon, (rect.centerx - icon.get_width() // 2, rect.centery - icon.get_height() // 2))

        old_clip = surface.get_clip()
        surface.set_clip(layout.content)
        y = layout.content.top - scroll_y
        for worker in visible_workers:
            row = pygame.Rect(layout.content.left, y, layout.content.width - (10 if layout.max_scroll else 0), _ROW_H)
            if row.bottom >= layout.content.top and row.top <= layout.content.bottom:
                pygame.draw.rect(surface, (48, 54, 66), row, border_radius=6)
                pygame.draw.rect(surface, (70, 78, 92), row, width=1, border_radius=6)
                title_text, task_text, detail_text = worker_summary(worker)
                surface.blit(body_font.render(title_text, True, (238, 240, 248)), (row.left + 12, row.top + 9))
                surface.blit(body_font.render(task_text, True, (205, 210, 220)), (row.left + 12, row.top + 34))
                surface.blit(small_font.render(detail_text, True, (160, 166, 178)), (row.left + 190, row.top + 34))
            y += _ROW_H + _ROW_GAP
        surface.set_clip(old_clip)

        if layout.max_scroll > 0:
            track = pygame.Rect(layout.content.right - 6, layout.content.top, 4, layout.content.height)
            pygame.draw.rect(surface, (54, 58, 68), track, border_radius=2)
            thumb_h = max(28, int(layout.content.height * layout.content.height / (layout.content.height + layout.max_scroll)))
            thumb_y = layout.content.top + int((layout.content.height - thumb_h) * (scroll_y / layout.max_scroll))
            pygame.draw.rect(surface, (120, 128, 146), (track.left, thumb_y, track.width, thumb_h), border_radius=2)

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        workers: tuple[Worker, ...],
        scroll_y: int = 0,
        worker_filter: str | None = None,
    ) -> str | None:
        layout = PopulationPanel.layout(surface, workers, scroll_y, worker_filter)
        if layout.close.collidepoint(pos):
            return "close"
        for worker_type, rect in layout.filters:
            if rect.collidepoint(pos):
                return "filter:all" if worker_type is None else f"filter:{worker_type}"
        if layout.frame.collidepoint(pos):
            return "inside"
        return None

    @staticmethod
    def worker_at(
        surface: pygame.Surface,
        pos: tuple[int, int],
        workers: tuple[Worker, ...],
        scroll_y: int = 0,
        worker_filter: str | None = None,
    ) -> Worker | None:
        """Return the worker row under the cursor, respecting current scroll."""
        layout = PopulationPanel.layout(surface, workers, scroll_y, worker_filter)
        if not layout.content.collidepoint(pos):
            return None
        visible_workers = _filtered_workers(workers, worker_filter)
        y = layout.content.top - PopulationPanel.clamp_scroll(surface, workers, scroll_y, worker_filter)
        for worker in visible_workers:
            row = pygame.Rect(layout.content.left, y, layout.content.width - (10 if layout.max_scroll else 0), _ROW_H)
            if row.collidepoint(pos):
                return worker
            y += _ROW_H + _ROW_GAP
        return None
