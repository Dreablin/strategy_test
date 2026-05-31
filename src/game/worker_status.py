"""Panel-facing worker and production status helpers."""

from __future__ import annotations

from typing import Any

from game import i18n
from game.buildings.base import Building
from game.worker_laboratory import (
    laboratory_active_scientists,
    laboratory_research_contributing_scientists,
)
from game.worker_models import Worker


def localized_status(status_id: str) -> str:
    """Return localized label for a stable status id."""
    sid = str(status_id).strip()
    for key in (f"status.{sid}", f"status.worker.{sid}"):
        label = i18n.t(key)
        if label != key:
            return label
    return sid.replace("_", " ").title()


def worker_status_for_building(manager: Any, building: Building) -> str:
    """Return panel-friendly worker status id: empty | on_the_way | assigned | ..."""
    if building.type_tag == "LABORATORY":
        if building.is_under_construction:
            return "empty"
        if not laboratory_active_scientists(manager._workers, building):
            return "empty"
        if not laboratory_research_contributing_scientists(manager._workers, building):
            return "on_the_way"
        return "assigned"
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
                return "on_the_way"
            if worker.state == "going_to_plant_tile":
                return "going_to_plant"
            if worker.state in {"arrived_plant_tile", "planting"}:
                return "planting"
            if worker.state in {"returning", "arrived_camp"}:
                return "returning"
            if worker.state == "return_path_blocked":
                return "path_blocked"
            if worker.state == "working":
                now_ms = int(manager._now_ms_fn())
                if worker.camp_wait_until_ms > now_ms:
                    return "resting"
                return "ready"
            if worker.state == "idle":
                return "idle"
            return "assigned"
        if worker.state in {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}:
            return "on_the_way"
        return "assigned"
    return "empty"


def production_status_for_building(manager: Any, building: Building) -> str:
    """Stable production status id for building panels."""
    if building.is_under_construction:
        return "under_construction"
    worker: Worker | None = None
    for candidate in manager._workers:
        if candidate.assigned_building is building:
            worker = candidate
            break
    if worker is None:
        if building.type_tag == "LABORATORY" and hasattr(building, "active"):
            return "no_worker" if getattr(building, "active", True) else "inactive"
        if building.type_tag == "WELL":
            return "no_worker" if getattr(building, "active", True) else "inactive"
        return "no_worker"

    if hasattr(building, "active") and not bool(getattr(building, "active")):
        return "inactive"
    if building.type_tag == "WELL":
        if worker.state == "resting":
            return "resting"
        if worker.state == "processing":
            return "processing"
        if int(getattr(building, "water_amount", lambda: 0)()) >= int(
            getattr(building, "water_capacity", lambda: 0)()
        ):
            return "output_full"
        return "ready"
    if building.type_tag == "FARM":
        if hasattr(building, "is_storage_full") and building.is_storage_full():
            return "storage_full"
        if worker.state in {"moving", "going_to_field", "returning"}:
            return "moving"
        if worker.state == "sowing":
            return "sowing"
        if worker.state == "harvesting":
            return "harvesting"
        if worker.state in {"resting", "working_field"}:
            return "resting" if manager._farm_has_actionable_field(building) else "no_fields_in_radius"
        if worker.state == "working":
            now_ms = int(manager._now_ms_fn())
            if worker.camp_wait_until_ms > now_ms:
                return "resting"
        return "ready"
    if building.type_tag == "VINEYARD_FARM":
        if hasattr(building, "grapes_amount") and hasattr(building, "grapes_capacity"):
            try:
                if int(building.grapes_amount()) >= int(building.grapes_capacity()):
                    return "storage_full"
            except (TypeError, ValueError):
                pass
        if worker.state in {"moving", "going_to_field", "going_to_vineyard", "returning"}:
            return "moving"
        if worker.state in {"harvesting_grapes", "vineyard_harvest_anim_done"}:
            return "harvesting"
        if worker.state == "arrived_vineyard":
            return "moving"
        if worker.state in {"resting", "working_field"}:
            return (
                "resting"
                if manager._vineyard_farm_has_actionable_ripe(building)
                else "no_ripe_vineyards_in_range"
            )
        if worker.state == "working":
            now_ms = int(manager._now_ms_fn())
            if worker.camp_wait_until_ms > now_ms:
                return "resting"
        return "ready"
    if building.type_tag == "SAWMILL":
        if worker.state == "resting":
            return "resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(getattr(building, "output_capacity", lambda: 0)()):
            return "output_full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "no_wood"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "MILL":
        if worker.state == "resting":
            return "resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "output_full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "no_wheat"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "BAKERY":
        if worker.state == "resting":
            return "resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "output_full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "no_flour"
        if int(getattr(building, "water_amount", lambda: 0)()) <= 0:
            return "no_water"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "CANTEEN":
        if worker.state == "resting":
            return "resting"
        if int(building.local_storage_amount("simple_meal")) >= int(building.local_storage_capacity("simple_meal")):
            return "output_full"
        if int(building.local_storage_amount("chicken")) <= 0:
            return "no_chicken"
        if int(building.local_storage_amount("bread")) <= 0:
            return "no_bread"
        if int(building.local_storage_amount("water")) <= 0:
            return "no_water"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "CHICKEN_FARM":
        if worker.state == "resting":
            return "resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "output_full"
        if int(getattr(building, "input_amount", lambda: 0)()) <= 0:
            return "no_grain"
        if int(getattr(building, "water_amount", lambda: 0)()) <= 0:
            return "no_water"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "COW_FARM":
        if worker.state == "resting":
            return "resting"
        if not building.has_recipe_output_space():
            return "output_full"
        if building.wheat_amount() < building.recipe_wheat_required():
            return "no_wheat"
        if building.water_amount() < building.recipe_water_required():
            return "no_water"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "WINERY":
        if worker.state == "resting":
            return "resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "output_full"
        if int(getattr(building, "input_amount", lambda: 0)()) < int(
            getattr(building, "recipe_input_count", lambda: 1)()
        ):
            return "no_grapes"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "RESTAURANT":
        if worker.state == "resting":
            return "resting"
        if int(getattr(building, "output_amount", lambda: 0)()) >= int(
            getattr(building, "output_capacity", lambda: 0)()
        ):
            return "output_full"
        if not building.has_recipe_inputs():
            return "missing_inputs"
        if worker.state == "processing":
            return "processing"
        return "ready"
    if building.type_tag == "IRON_MINE":
        if worker.state == "resting":
            return "resting"
        if hasattr(building, "is_storage_full") and building.is_storage_full():
            return "storage_full"
        if worker.state == "mining":
            return "mining"
        return "ready"
    if hasattr(building, "is_storage_full") and building.is_storage_full():
        return "storage_full"

    moving_states = {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}
    if worker.state in moving_states:
        return "on_the_way"
    if worker.state in {"chopping", "mining", "planting"}:
        return "gathering"
    if worker.state == "depositing":
        return "depositing"
    if worker.state in {"arrived_tree", "arrived_stone", "arrived_plant_tile"}:
        return "at_resource"
    if worker.state == "arrived_camp":
        return "at_camp"
    if worker.state == "working":
        now_ms = int(manager._now_ms_fn())
        if worker.camp_wait_until_ms > now_ms:
            return "resting"
        return "ready"
    if worker.state == "idle":
        return "waiting_target"
    if worker.state == "resting":
        return "resting"
    return "unknown"
