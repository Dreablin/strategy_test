"""Worker state models."""

from __future__ import annotations

from dataclasses import dataclass

from game.buildings.base import Building
from game.characteristics import Characteristics
from game.config import WORKER_TILE_TRAVEL_MS
from game.worker_constants import CHOP_DURATION_MS
from game.worker_satiety import MAX_WORKER_SATIETY


@dataclass(slots=True)
class TransportTask:
    resource: str
    source: Building
    target: Building
    priority: int = 0
    returning_to_town_hall: bool = False
    purpose: str = "generic"


class Worker:
    """One worker: type tag, optional assigned building, idle flag, stand tile for rendering."""

    __slots__ = (
        "type_tag",
        "assigned_building",
        "idle",
        "stand_tile",
        "state",
        "current_tile",
        "target_tile",
        "path",
        "segment_started_ms",
        "segment_progress",
        "arrival_ms",
        "camp_wait_until_ms",
        "carrying",
        "target_tree",
        "chop_started_ms",
        "chop_duration_ms",
        "characteristics",
        "transport_task",
        "satiety",
        "satiety_last_sample_ms",
    )

    def __init__(self, type_tag: str, *, stand_tile: tuple[int, int] = (17, 19)) -> None:
        self.type_tag = type_tag
        self.satiety = MAX_WORKER_SATIETY
        self.satiety_last_sample_ms = -1
        self.assigned_building: Building | None = None
        self.idle = True
        self.stand_tile: tuple[int, int] = stand_tile
        self.state = "idle"
        self.current_tile = stand_tile
        self.target_tile: tuple[int, int] | None = None
        self.path: list[tuple[int, int]] = []
        self.segment_started_ms = 0
        self.segment_progress = 0.0
        self.arrival_ms = 0
        self.camp_wait_until_ms = 0
        self.carrying: str | None = None
        self.target_tree: tuple[int, int] | None = None
        self.chop_started_ms = 0
        self.chop_duration_ms = CHOP_DURATION_MS
        self.characteristics = Characteristics()
        self.transport_task: TransportTask | None = None

    def start_move(self, path: list[tuple[int, int]], started_ms: int, *, move_state: str = "moving") -> None:
        if len(path) < 2:
            self.path = [self.current_tile, self.current_tile]
            self.target_tile = self.current_tile
            self.segment_started_ms = int(started_ms)
            self.arrival_ms = int(started_ms)
            self.segment_progress = 0.0
            if move_state == "going_to_tree":
                self.state = "going_to_tree"
            elif move_state == "going_to_stone":
                self.state = "going_to_stone"
            elif move_state == "going_to_plant_tile":
                self.state = "going_to_plant_tile"
            elif move_state == "returning":
                self.state = "returning"
            else:
                self.state = "working"
            self.idle = False
            return
        self.path = list(path)
        self.current_tile = self.path[0]
        self.target_tile = self.path[1]
        self.segment_started_ms = int(started_ms)
        self.segment_progress = 0.0
        self.state = move_state
        self.idle = False

    def update(self, now_ms: int) -> None:
        if self.state not in {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "going_to_field", "returning"} or self.target_tile is None:
            return
        travel_ms = self._effective_travel_ms()
        elapsed = max(0, int(now_ms) - self.segment_started_ms)
        while elapsed >= travel_ms:
            self.current_tile = self.target_tile
            self.path = self.path[1:] if self.path else []
            if len(self.path) >= 2:
                self.target_tile = self.path[1]
                self.segment_started_ms += travel_ms
                self.segment_progress = 0.0
                elapsed = max(0, int(now_ms) - self.segment_started_ms)
                continue
            self.target_tile = self.current_tile
            self.segment_progress = 1.0
            self.arrival_ms = self.segment_started_ms + travel_ms
            if self.state == "going_to_tree":
                self.state = "arrived_tree"
            elif self.state == "going_to_stone":
                self.state = "arrived_stone"
            elif self.state == "going_to_plant_tile":
                self.state = "arrived_plant_tile"
            elif self.state == "going_to_field":
                self.state = "arrived_field"
            elif self.state == "returning":
                self.state = "arrived_camp"
            else:
                self.state = "working"
            self.idle = False
            self.stand_tile = self.current_tile
            return
        self.segment_progress = elapsed / travel_ms

    def _effective_travel_ms(self) -> int:
        speed = self.characteristics.move_speed_mult
        if speed <= 0.0:
            return WORKER_TILE_TRAVEL_MS
        return max(1, int(round(WORKER_TILE_TRAVEL_MS / speed)))
