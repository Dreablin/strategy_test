"""Panel-facing worker and production status helpers."""

from __future__ import annotations

from typing import Any

from game.buildings.base import Building
from game.worker_models import Worker


def worker_status_for_building(manager: Any, building: Building) -> str:
    """Return panel-friendly worker status: empty | on the way | assigned."""
    if building.is_under_construction:
        for worker in manager._workers:
            if worker.assigned_building is building:
                return "resting"
        return "empty"
    for worker in manager._workers:
        if worker.assigned_building is not building:
            continue
        if building.type_tag in {"FARM", "VINEYARD_FARM"}:
            if worker.state in {"moving", "going_to_field", "going_to_vineyard", "returning"}:
                return "moving"
            if worker.state == "sowing":
                return "sowing"
            if worker.state in {"harvesting", "harvesting_grapes", "vineyard_harvest_anim_done"}:
                return "harvesting"
            if worker.state in {"arrived_vineyard"}:
                return "moving"
            if worker.state in {"resting", "working_field"}:
                return "resting"
            if worker.state == "working":
                now_ms = int(manager._now_ms_fn())
                if worker.camp_wait_until_ms > now_ms:
                    return "resting"
            return "assigned"
        if worker.type_tag == "FORESTER":
            if worker.state == "moving":
                return "on the way"
            if worker.state == "going_to_plant_tile":
                return "going to plant"
            if worker.state in {"arrived_plant_tile", "planting"}:
                return "planting"
            if worker.state in {"returning", "arrived_camp"}:
                return "returning"
            if worker.state == "return_path_blocked":
                return "path blocked"
            if worker.state == "working":
                now_ms = int(manager._now_ms_fn())
                if worker.camp_wait_until_ms > now_ms:
                    return "resting"
                return "ready"
            if worker.state == "idle":
                return "idle"
            return "assigned"
        if worker.state in {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}:
            return "on the way"
        return "assigned"
    return "empty"


def production_status_for_building(manager: Any, building: Building) -> str:
    """Human-readable production status for building panels."""
    if building.is_under_construction:
        return "Under construction"
    worker: Worker | None = None
    for candidate in manager._workers:
        if candidate.assigned_building is building:
            worker = candidate
            break
    if worker is None:
        if building.type_tag == "WELL":
            return "No worker" if getattr(building, "active", True) else "Inactive"
        return "No worker"

    if hasattr(building, "active") and not bool(getattr(building, "active")):
        return "Inactive"
    if building.type_tag == "WELL":
        if worker.state == "resting":
            return "Resting"
        if worker.state == "processing":
            return "Processing"
        if int(getattr(building, "water_amount", lambda: 0)()) >= int(
            getattr(building, "water_capacity", lambda: 0)()
        ):
            return "Output full"
        return "Ready"
    if building.type_tag == "FARM":
        if hasattr(building, "is_storage_full") and building.is_storage_full():
            return "Storage full"
        if worker.state in {"moving", "going_to_field", "returning"}:
            return "Moving"
        if worker.state == "sowing":
            return "Sowing"
        if worker.state == "harvesting":
            return "Harvesting"
        if worker.state in {"resting", "working_field"}:
            return "Resting" if manager._farm_has_actionable_field(building) else "No fields in radius"
        if worker.state == "working":
            now_ms = int(manager._now_ms_fn())
            if worker.camp_wait_until_ms > now_ms:
                return "Resting"
        return "Ready"
    if building.type_tag == "VINEYARD_FARM":
        if hasattr(building, "grapes_amount") and hasattr(building, "grapes_capacity"):
            try:
                if int(building.grapes_amount()) >= int(building.grapes_capacity()):
                    return "Storage full"
            except (TypeError, ValueError):
                pass
        if worker.state in {"moving", "going_to_field", "going_to_vineyard", "returning"}:
            return "Moving"
        if worker.state in {"harvesting_grapes", "vineyard_harvest_anim_done"}:
            return "Harvesting"
        if worker.state == "arrived_vineyard":
            return "Moving"
        if worker.state in {"resting", "working_field"}:
            return (
                "Resting"
                if manager._vineyard_farm_has_actionable_ripe(building)
                else "No ripe vineyards in range"
            )
        if worker.state == "working":
            now_ms = int(manager._now_ms_fn())
            if worker.camp_wait_until_ms > now_ms:
                return "Resting"
        return "Ready"
    if building.type_tag == "SAWMILL":
        if worker.state == "resting":
            return "Resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(getattr(building, "output_capacity", lambda: 0)()):
            return "Output full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "No wood"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "MILL":
        if worker.state == "resting":
            return "Resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "Output full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "No wheat"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "BAKERY":
        if worker.state == "resting":
            return "Resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "Output full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "No flour"
        if int(getattr(building, "water_amount", lambda: 0)()) <= 0:
            return "No water"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "CANTEEN":
        if worker.state == "resting":
            return "Resting"
        if int(building.local_storage_amount("simple_meal")) >= int(building.local_storage_capacity("simple_meal")):
            return "Output full"
        if int(building.local_storage_amount("chicken")) <= 0:
            return "No chicken"
        if int(building.local_storage_amount("bread")) <= 0:
            return "No bread"
        if int(building.local_storage_amount("water")) <= 0:
            return "No water"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "CHICKEN_FARM":
        if worker.state == "resting":
            return "Resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "Output full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "No grain"
        if int(getattr(building, "water_amount", lambda: 0)()) <= 0:
            return "No water"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "COW_FARM":
        if worker.state == "resting":
            return "Resting"
        if not building.has_recipe_output_space():
            return "Output full"
        if building.wheat_amount() < building.recipe_wheat_required():
            return "No wheat"
        if building.water_amount() < building.recipe_water_required():
            return "No water"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "WINERY":
        if worker.state == "resting":
            return "Resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "Output full"
        if int(getattr(building, "input_amount", lambda: 0)()) < int(
            getattr(building, "recipe_input_count", lambda: 1)()
        ):
            return "No grapes"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "RESTAURANT":
        if worker.state == "resting":
            return "Resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "Output full"
        if not building.has_recipe_inputs():
            return "Missing inputs"
        if worker.state == "processing":
            return "Processing"
        return "Ready"
    if building.type_tag == "IRON_MINE":
        if worker.state == "resting":
            return "Resting"
        if hasattr(building, "is_storage_full") and building.is_storage_full():
            return "Storage full"
        if worker.state == "mining":
            return "Mining"
        return "Ready"
    if hasattr(building, "is_storage_full") and building.is_storage_full():
        return "Storage full"

    moving_states = {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}
    if worker.state in moving_states:
        return "On the way"
    if worker.state in {"chopping", "mining", "planting"}:
        return "Gathering"
    if worker.state == "depositing":
        return "Depositing"
    if worker.state in {"arrived_tree", "arrived_stone", "arrived_plant_tile"}:
        return "At resource"
    if worker.state == "arrived_camp":
        return "At camp"
    if worker.state == "working":
        now_ms = int(manager._now_ms_fn())
        if worker.camp_wait_until_ms > now_ms:
            return "Resting"
        return "Ready"
    if worker.state == "idle":
        return "Waiting target"
    if worker.state == "resting":
        return "Resting"
    return "Unknown"


