"""Processor worker runtime helpers for WorkerManager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from game.buildings.well import WELL_CYCLE_MS, WELL_REST_MS
from game.worker_geometry import building_center_tile
from game.worker_hunger import try_hunger_canteen_after_completed_cycle
from game.worker_models import Worker


@dataclass(frozen=True)
class ProcessorSpec:
    building_type: str
    duration_ms: Callable[[Any], int]
    rest_ms: int
    has_inputs: Callable[[Any], bool]
    consume_inputs: Callable[[Any], None]
    add_output: Callable[[Any], None]
    rest_ms_for: Callable[[Any], int] | None = None


def _output_has_space(building: Any) -> bool:
    return getattr(building, "output_amount", lambda: 0)() < getattr(
        building, "output_capacity", lambda: 0
    )()


def _recipe_output_space_ok(building: Any) -> bool:
    """Single-output buildings use ``output_*``; Cow Farm uses ``has_recipe_output_space``."""
    if hasattr(building, "has_recipe_output_space"):
        return bool(building.has_recipe_output_space())
    if hasattr(building, "recipe_output"):
        return _configured_recipe_has_output_space(building)
    return _output_has_space(building)


def _multi_input_has_recipe(building: Any) -> bool:
    return bool(getattr(building, "has_recipe_inputs", lambda: False)())


def _has_input_and_output_space(building: Any, has_recipe: Callable[[Any], bool]) -> bool:
    return has_recipe(building) and _recipe_output_space_ok(building)


def _building_cycle_duration_ms(building: Any) -> int:
    return max(1, int(getattr(building, "cycle_ms")()))


def _building_rest_ms(building: Any) -> int:
    return max(0, int(getattr(building, "rest_ms")()))


def _recipe_input(building: Any) -> dict[str, int]:
    raw = getattr(building, "recipe_input")()
    return {str(resource): int(count) for resource, count in raw.items()}


def _recipe_output(building: Any) -> dict[str, int]:
    raw = getattr(building, "recipe_output")()
    return {str(resource): int(count) for resource, count in raw.items()}


def _has_local_storage_resource(building: Any, resource: str) -> bool:
    resources = getattr(building, "local_storage_resources", lambda: ())()
    return str(resource) in resources


def _resource_amount(building: Any, resource: str) -> int:
    resource = str(resource)
    if _has_local_storage_resource(building, resource):
        return int(building.local_storage_amount(resource))
    specific = getattr(building, f"{resource}_amount", None)
    if callable(specific):
        return int(specific())
    if resource in {"wood", "wheat", "flour", "grapes"}:
        return int(getattr(building, "input_amount")())
    if resource == "water" and hasattr(building, "water_amount"):
        return int(building.water_amount())
    raise KeyError(resource)


def _output_resource_amount(building: Any, resource: str) -> int:
    resource = str(resource)
    if _has_local_storage_resource(building, resource):
        return int(building.local_storage_amount(resource))
    specific = getattr(building, f"{resource}_amount", None)
    if callable(specific):
        return int(specific())
    return int(getattr(building, "output_amount")())


def _resource_capacity(building: Any, resource: str, *, output: bool) -> int:
    resource = str(resource)
    if _has_local_storage_resource(building, resource):
        return int(building.local_storage_capacity(resource))
    specific = getattr(building, f"{resource}_capacity", None)
    if callable(specific):
        return int(specific())
    if output:
        return int(getattr(building, "output_capacity")())
    if resource == "water" and hasattr(building, "water_capacity"):
        return int(building.water_capacity())
    return int(getattr(building, "input_capacity")())


def _configured_recipe_has_inputs(building: Any) -> bool:
    return all(_resource_amount(building, resource) >= needed for resource, needed in _recipe_input(building).items())


def _configured_recipe_has_output_space(building: Any) -> bool:
    for resource, amount in _recipe_output(building).items():
        free = _resource_capacity(building, resource, output=True) - _output_resource_amount(building, resource)
        if free < amount:
            return False
    return True


def _take_input_resource(building: Any, resource: str, amount: int) -> None:
    resource = str(resource)
    if _has_local_storage_resource(building, resource):
        building.take_local_storage(resource, amount)
        return
    method_by_resource = {
        "wood": "take_wood_in",
        "wheat": "take_wheat_in",
        "flour": "take_flour_in",
        "water": "take_water_in",
        "grapes": "take_grapes",
    }
    method = getattr(building, method_by_resource[resource])
    method(amount)


def _add_output_resource(building: Any, resource: str, amount: int) -> None:
    resource = str(resource)
    if _has_local_storage_resource(building, resource):
        building.add_local_storage(resource, amount)
        return
    method_by_resource = {
        "boards": "add_boards_out",
        "flour": "add_flour_out",
        "bread": "add_bread_out",
        "chicken": "add_chicken_out",
        "wine": "add_wine",
    }
    method = getattr(building, method_by_resource[resource])
    method(amount)


def _consume_configured_recipe_inputs(building: Any) -> None:
    for resource, count in _recipe_input(building).items():
        _take_input_resource(building, resource, count)


def _add_configured_recipe_outputs(building: Any) -> None:
    for resource, count in _recipe_output(building).items():
        _add_output_resource(building, resource, count)


def _spec_rest_ms(spec: ProcessorSpec, building: Any) -> int:
    if spec.rest_ms_for is not None:
        return max(0, int(spec.rest_ms_for(building)))
    return max(0, int(spec.rest_ms))


class WorkerProcessingMixin:
    def _update_sawyer(self, worker: Worker, now_ms: int, world: Any) -> None:
        self._update_processor_worker(worker, now_ms, SAWMILL_PROCESSOR, world)

    def _update_miller(self, worker: Worker, now_ms: int, world: Any) -> None:
        self._update_processor_worker(worker, now_ms, MILL_PROCESSOR, world)

    def _update_baker(self, worker: Worker, now_ms: int, world: Any) -> None:
        self._update_processor_worker(worker, now_ms, BAKERY_PROCESSOR, world)

    def _update_cook(self, worker: Worker, now_ms: int, world: Any) -> None:
        building = worker.assigned_building
        if building is not None and building.type_tag == "RESTAURANT":
            self._update_processor_worker(worker, now_ms, RESTAURANT_PROCESSOR, world)
        else:
            self._update_processor_worker(worker, now_ms, CANTEEN_PROCESSOR, world)

    def _update_animal_herder(self, worker: Worker, now_ms: int, world: Any) -> None:
        building = worker.assigned_building
        if building is None:
            return
        if building.type_tag == "CHICKEN_FARM":
            self._update_processor_worker(worker, now_ms, CHICKEN_FARM_PROCESSOR, world)
        elif building.type_tag == "COW_FARM":
            self._update_processor_worker(worker, now_ms, COW_FARM_PROCESSOR, world)

    def _update_waterman(self, worker: Worker, now_ms: int, world: Any) -> None:
        self._update_processor_worker(worker, now_ms, WELL_PROCESSOR, world)

    def _update_winemaker(self, worker: Worker, now_ms: int, world: Any) -> None:
        self._update_processor_worker(worker, now_ms, WINERY_PROCESSOR, world)

    def _update_restaurant_cook(self, worker: Worker, now_ms: int, world: Any) -> None:
        self._update_processor_worker(worker, now_ms, RESTAURANT_PROCESSOR, world)

    def _update_processor_worker(
        self, worker: Worker, now_ms: int, spec: ProcessorSpec, world: Any
    ) -> None:
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
            worker.camp_wait_until_ms = int(now_ms) + _spec_rest_ms(spec, building)
            worker.current_tile = center_tile
            worker.idle = False
            reg = getattr(self, "_registry", None)
            if world is not None and reg is not None:
                try_hunger_canteen_after_completed_cycle(
                    worker,
                    world=world,
                    registry=reg,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )
            return
        if not active:
            worker.state = "resting"
            worker.current_tile = center_tile
            return
        if not _has_input_and_output_space(building, spec.has_inputs):
            self._try_blocked_cycle_hunger(worker, now_ms)
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
    duration_ms=_building_cycle_duration_ms,
    rest_ms=0,
    has_inputs=_configured_recipe_has_inputs,
    consume_inputs=_consume_configured_recipe_inputs,
    add_output=_add_configured_recipe_outputs,
    rest_ms_for=_building_rest_ms,
)

MILL_PROCESSOR = ProcessorSpec(
    building_type="MILL",
    duration_ms=_building_cycle_duration_ms,
    rest_ms=0,
    has_inputs=_configured_recipe_has_inputs,
    consume_inputs=_consume_configured_recipe_inputs,
    add_output=_add_configured_recipe_outputs,
    rest_ms_for=_building_rest_ms,
)

BAKERY_PROCESSOR = ProcessorSpec(
    building_type="BAKERY",
    duration_ms=_building_cycle_duration_ms,
    rest_ms=0,
    has_inputs=_configured_recipe_has_inputs,
    consume_inputs=_consume_configured_recipe_inputs,
    add_output=_add_configured_recipe_outputs,
    rest_ms_for=_building_rest_ms,
)

CHICKEN_FARM_PROCESSOR = ProcessorSpec(
    building_type="CHICKEN_FARM",
    duration_ms=_building_cycle_duration_ms,
    rest_ms=0,
    has_inputs=_configured_recipe_has_inputs,
    consume_inputs=_consume_configured_recipe_inputs,
    add_output=_add_configured_recipe_outputs,
    rest_ms_for=_building_rest_ms,
)


def _cow_cycle_duration_ms(building: Any) -> int:
    return max(1, int(getattr(building, "processing_duration_ms", 1)))


def _cow_consume_recipe(farm: Any) -> None:
    farm.take_wheat_in(farm.recipe_wheat_required())
    farm.take_water_in(farm.recipe_water_required())


def _cow_add_recipe_outputs(farm: Any) -> None:
    farm.add_beef_out(farm.recipe_beef_output())
    farm.add_hide_out(farm.recipe_hide_output())


COW_FARM_PROCESSOR = ProcessorSpec(
    building_type="COW_FARM",
    duration_ms=_cow_cycle_duration_ms,
    rest_ms=0,
    has_inputs=_multi_input_has_recipe,
    consume_inputs=_cow_consume_recipe,
    add_output=_cow_add_recipe_outputs,
    rest_ms_for=lambda b: max(0, int(b.production_rest_ms())),
)

CANTEEN_PROCESSOR = ProcessorSpec(
    building_type="CANTEEN",
    duration_ms=_building_cycle_duration_ms,
    rest_ms=0,
    has_inputs=_configured_recipe_has_inputs,
    consume_inputs=_consume_configured_recipe_inputs,
    add_output=_add_configured_recipe_outputs,
    rest_ms_for=_building_rest_ms,
)

WELL_PROCESSOR = ProcessorSpec(
    building_type="WELL",
    duration_ms=lambda b: max(1, int(getattr(b, "processing_duration_ms", WELL_CYCLE_MS))),
    rest_ms=int(WELL_REST_MS),
    has_inputs=lambda _b: True,
    consume_inputs=lambda _b: None,
    add_output=lambda b: b.add_water_in(1),
    rest_ms_for=lambda b: max(0, int(getattr(b, "rest_duration_ms", WELL_REST_MS))),
)

WINERY_PROCESSOR = ProcessorSpec(
    building_type="WINERY",
    duration_ms=lambda b: max(1, b.cycle_ms()),
    rest_ms=0,
    has_inputs=_multi_input_has_recipe,
    consume_inputs=lambda winery: winery.take_grapes(winery.recipe_input_count()),
    add_output=lambda winery: winery.add_wine(winery.recipe_output_count()),
    rest_ms_for=lambda b: max(0, b.rest_ms()),
)


def _consume_restaurant_inputs(building: Any) -> None:
    for resource, count in building.recipe_input_count().items():
        building.take_local_storage(resource, count)


def _add_restaurant_output(building: Any) -> None:
    building.add_local_storage("elite_meal", building.recipe_output_count())


RESTAURANT_PROCESSOR = ProcessorSpec(
    building_type="RESTAURANT",
    duration_ms=lambda b: max(1, b.cycle_ms()),
    rest_ms=0,
    has_inputs=_multi_input_has_recipe,
    consume_inputs=_consume_restaurant_inputs,
    add_output=_add_restaurant_output,
    rest_ms_for=lambda b: max(0, b.rest_ms()),
)
