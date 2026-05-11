"""Centered modal panel: worker state and current transport task."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.resource_catalog import resource_display_label
from game.worker_models import Worker
from game.worker_satiety import MAX_WORKER_SATIETY, clamp_worker_satiety

_PANEL_W = 420
_PANEL_PAD = 16
_ROW = 26
_CLOSE = 28

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
    "wood": "Wood",
    "stone": "Stone",
    "iron": "Iron",
    "boards": "Boards",
    "wheat": "Wheat",
    "flour": "Flour",
    "bread": "Bread",
    "chicken": "Chicken",
    "beef": "Beef",
    "hide": "Hide",
    "grapes": "Grapes",
    "water": "Water",
}

_PURPOSE_LABEL: dict[str, str] = {
    "generic": "Transport",
    "construction": "Construction delivery",
    "return": "Return to Town Hall",
}

_STATE_LABEL: dict[str, str] = {
    "going_to_canteen": "Going to canteen",
    "waiting_for_meal": "Waiting for meal",
    "eating": "Eating",
}


@dataclass(frozen=True, slots=True)
class WorkerPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect


def _label(value: str | None, labels: dict[str, str]) -> str:
    if value is None:
        return "none"
    if value in labels:
        return labels[value]
    return resource_display_label(value)


def _building_name(building) -> str:
    tag = str(getattr(building, "type_tag", ""))
    return _label(tag, _BUILDING_LABEL)


def _move_speed_line(worker: Worker) -> str:
    speed = worker.characteristics.move_speed_mult
    return f"Move speed: {speed:.2f}x ({worker.effective_travel_ms()} ms/tile)"


def _worker_lines(worker: Worker) -> list[str]:
    sat = clamp_worker_satiety(int(getattr(worker, "satiety", 0)))
    state = _STATE_LABEL.get(str(worker.state), str(worker.state))
    lines = [
        f"State: {state}",
        f"Satiety: {sat}/{MAX_WORKER_SATIETY}",
        _move_speed_line(worker),
        f"Assigned: {_building_name(worker.assigned_building) if worker.assigned_building is not None else 'none'}",
        f"Carrying: {_label(worker.carrying, _RESOURCE_LABEL)}",
    ]
    task = worker.transport_task
    if task is None:
        lines.append("Task: none")
        return lines

    lines.extend(
        [
            f"Task: {_label(task.purpose, _PURPOSE_LABEL)}",
            f"Resource: {_label(task.resource, _RESOURCE_LABEL)}",
            f"From: {_building_name(task.source)}",
            f"To: {_building_name(task.target)}",
        ]
    )
    if task.returning_to_town_hall:
        lines.append("Returning: yes")
    return lines


class WorkerPanel:
    """Small read-only worker panel, mirroring building modal behavior."""

    @staticmethod
    def body_lines(worker: Worker) -> list[str]:
        """Body text lines under the title (includes satiety and task summary)."""
        return _worker_lines(worker)

    @staticmethod
    def layout(surface: pygame.Surface, worker: Worker) -> WorkerPanelLayout:
        sw, sh = surface.get_size()
        row_count = len(WorkerPanel.body_lines(worker))
        h = _PANEL_PAD * 2 + _ROW + 8 + row_count * _ROW + 8
        frame = pygame.Rect(sw // 2 - _PANEL_W // 2, sh // 2 - h // 2, _PANEL_W, h)
        close = pygame.Rect(
            frame.right - _PANEL_PAD - _CLOSE,
            frame.top + _PANEL_PAD,
            _CLOSE,
            _CLOSE,
        )
        return WorkerPanelLayout(frame=frame, close=close)

    @staticmethod
    def draw(surface: pygame.Surface, worker: Worker) -> None:
        layout = WorkerPanel.layout(surface, worker)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)

        title_font = pygame.font.Font(None, 28)
        body_font = pygame.font.Font(None, 22)
        title = title_font.render(_label(worker.type_tag, _WORKER_LABEL), True, (238, 240, 248))
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

        y = layout.frame.top + _PANEL_PAD + _ROW + 8
        for line in WorkerPanel.body_lines(worker):
            surface.blit(body_font.render(line, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
            y += _ROW

    @staticmethod
    def click_action(surface: pygame.Surface, pos: tuple[int, int], worker: Worker) -> str | None:
        layout = WorkerPanel.layout(surface, worker)
        if layout.close.collidepoint(pos):
            return "close"
        return None
