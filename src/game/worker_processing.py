"""Processor worker runtime helpers for WorkerManager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from game.worker_constants import (
    ANIMAL_HERDER_REST_MS,
    BAKER_REST_MS,
    BAKERY_CYCLE_MS,
    CHICKEN_FARM_CYCLE_MS,
    MILLER_REST_MS,
    MILL_BASE_CYCLE_MS,
    MILL_MIN_CYCLE_MS,
    SAWMILL_BASE_CYCLE_MS,
    SAWMILL_MIN_CYCLE_MS,
    SAWYER_REST_MS,
)
from game.worker_geometry import building_center_tile
from game.worker_models import Worker


@dataclass(frozen=True)
class ProcessorSpec:
    building_type: str
    duration_ms: Callable[[Any], int]
    rest_ms: int
    has_inputs: Callable[[Any], bool]
    consume_inputs: Callable[[Any], None]
    add_output: Callable[[Any], None]


def _output_has_space(building: Any) -> bool:
    return getattr(building, "output_amount", lambda: 0)() < getattr(
        building, "output_capacity", lambda: 0
    )()


def _single_input_has_recipe(building: Any) -> bool:
    return getattr(building, "input_amount", lambda: 0)() > 0


def _multi_input_has_recipe(building: Any) -> bool:
    return bool(getattr(building, "has_recipe_inputs", lambda: False)())


def _has_input_and_output_space(building: Any, has_recipe: Callable[[Any], bool]) -> bool:
    return has_recipe(building) and _output_has_space(building)


def _fixed_duration(duration_ms: int) -> Callable[[Any], int]:
    def duration(_building: Any) -> int:
        return duration_ms

    return duration


class WorkerProcessingMixin:
    @staticmethod
    def _sawmill_cycle_duration_ms(sawmill: Any) -> int:
        level = max(1, int(getattr(sawmill, "level", 1)))
        mult = 1.0 - 0.02 * float(level - 1)
        effective = int(round(SAWMILL_BASE_CYCLE_MS * mult))
        return max(SAWMILL_MIN_CYCLE_MS, effective)

    @staticmethod
    def _mill_cycle_duration_ms(mill: Any) -> int:
        level = max(1, int(getattr(mill, "level", 1)))
        mult = 1.0 - 0.02 * float(level - 1)
        effective = int(round(MILL_BASE_CYCLE_MS * mult))
        return max(MILL_MIN_CYCLE_MS, effective)

    @staticmethod
    def _update_sawyer(worker: Worker, now_ms: int, world: Any) -> None:
        _ = world
        WorkerProcessingMixin._update_processor_worker(worker, now_ms, SAWMILL_PROCESSOR)

    @staticmethod
    def _update_miller(worker: Worker, now_ms: int, world: Any) -> None:
        _ = world
        WorkerProcessingMixin._update_processor_worker(worker, now_ms, MILL_PROCESSOR)

    @staticmethod
    def _update_baker(worker: Worker, now_ms: int, world: Any) -> None:
        _ = world
        WorkerProcessingMixin._update_processor_worker(worker, now_ms, BAKERY_PROCESSOR)

    @staticmethod
    def _update_animal_herder(worker: Worker, now_ms: int, world: Any) -> None:
        _ = world
        WorkerProcessingMixin._update_processor_worker(worker, now_ms, CHICKEN_FARM_PROCESSOR)

    @staticmethod
    def _update_processor_worker(worker: Worker, now_ms: int, spec: ProcessorSpec) -> None:
        building = worker.assigned_building
        if building is None or building.type_tag != spec.building_type:
            return
        if building.is_under_construction:
            return
        center_tile = building_center_tile(building)
        if worker.state in {"working", "resting", "processing"} and worker.current_tile != center_tile:
            worker.current_tile = center_tile
            if worker.state == "processing":
                worker.state = "working"
                building.processing_started_ms = 0
            return
        active = bool(getattr(building, "active", False))
        if worker.state == "resting":
            if now_ms < worker.camp_wait_until_ms:
                return
            if not active:
                worker.current_tile = center_tile
                return
            worker.state = "working"
            worker.camp_wait_until_ms = 0
            worker.idle = False
        if worker.state == "resting":
            return
        if worker.state == "processing":
            started = int(getattr(building, "processing_started_ms", 0))
            if started <= 0:
                worker.state = "working"
                return
            duration = spec.duration_ms(building)
            building.processing_duration_ms = duration
            if now_ms - started < duration:
                return
            if _has_input_and_output_space(building, spec.has_inputs):
                spec.consume_inputs(building)
                spec.add_output(building)
            building.processing_started_ms = 0
            worker.state = "resting"
            worker.camp_wait_until_ms = int(now_ms) + spec.rest_ms
            worker.current_tile = center_tile
            worker.idle = False
            return
        if not active:
            worker.state = "resting"
            worker.current_tile = center_tile
            return
        if not _has_input_and_output_space(building, spec.has_inputs):
            return
        if worker.state != "working":
            return
        if int(getattr(building, "processing_started_ms", 0)) <= 0:
            building.processing_started_ms = int(now_ms)
        building.processing_duration_ms = spec.duration_ms(building)
        worker.state = "processing"
        worker.idle = False


SAWMILL_PROCESSOR = ProcessorSpec(
    building_type="SAWMILL",
    duration_ms=WorkerProcessingMixin._sawmill_cycle_duration_ms,
    rest_ms=SAWYER_REST_MS,
    has_inputs=_single_input_has_recipe,
    consume_inputs=lambda sawmill: sawmill.take_wood_in(1),
    add_output=lambda sawmill: sawmill.add_boards_out(1),
)

MILL_PROCESSOR = ProcessorSpec(
    building_type="MILL",
    duration_ms=WorkerProcessingMixin._mill_cycle_duration_ms,
    rest_ms=MILLER_REST_MS,
    has_inputs=_single_input_has_recipe,
    consume_inputs=lambda mill: mill.take_wheat_in(1),
    add_output=lambda mill: mill.add_flour_out(1),
)

BAKERY_PROCESSOR = ProcessorSpec(
    building_type="BAKERY",
    duration_ms=_fixed_duration(BAKERY_CYCLE_MS),
    rest_ms=BAKER_REST_MS,
    has_inputs=_multi_input_has_recipe,
    consume_inputs=lambda bakery: (bakery.take_flour_in(1), bakery.take_water_in(1)),
    add_output=lambda bakery: bakery.add_bread_out(1),
)

CHICKEN_FARM_PROCESSOR = ProcessorSpec(
    building_type="CHICKEN_FARM",
    duration_ms=_fixed_duration(CHICKEN_FARM_CYCLE_MS),
    rest_ms=ANIMAL_HERDER_REST_MS,
    has_inputs=_multi_input_has_recipe,
    consume_inputs=lambda farm: (farm.take_wheat_in(1), farm.take_water_in(1)),
    add_output=lambda farm: farm.add_chicken_out(1),
)
