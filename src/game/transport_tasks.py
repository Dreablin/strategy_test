"""Transport task builders for carriers."""

from __future__ import annotations

from typing import Any

from game.buildings.base import Building
from game.worker_models import TransportTask

PROCESSOR_INPUT_ADD_METHOD_BY_RESOURCE: dict[str, str] = {
    "wheat": "add_wheat_in",
    "wood": "add_wood_in",
    "flour": "add_flour_in",
}


def construction_transport_tasks(
    registry: Any,
    inbound_counts: dict[tuple[int, str], int] | None = None,
) -> list[TransportTask]:
    """Build high-priority transport tasks from Town Hall to construction sites."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None or not hasattr(town_hall, "warehouse_amount"):
        return []
    tasks: list[TransportTask] = []
    available_by_resource: dict[str, int] = {}
    for building in buildings:
        if not getattr(building, "is_under_construction", False):
            continue
        site = getattr(building, "construction_site", None)
        if site is None:
            continue
        for resource, need in site.remaining_resources().items():
            key = str(resource).lower()
            inbound = int((inbound_counts or {}).get((id(building), key), 0))
            need_after_inbound = max(0, int(need) - inbound)
            if need_after_inbound <= 0:
                continue
            if key not in available_by_resource:
                available_by_resource[key] = max(0, int(town_hall.warehouse_amount(resource)))
            available = available_by_resource[key]
            count = min(need_after_inbound, max(0, available))
            available_by_resource[key] = max(0, available - count)
            for _ in range(count):
                tasks.append(
                    TransportTask(
                        resource=key,
                        source=town_hall,
                        target=building,
                        priority=10,
                        purpose="construction",
                    )
                )
    return tasks


def sawmill_input_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority refill tasks from Town Hall to active sawmills."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None or not hasattr(town_hall, "warehouse_amount"):
        return []
    available = int(town_hall.warehouse_amount("wood"))
    if available <= 0:
        return []
    tasks: list[TransportTask] = []
    remaining_wood = available
    for building in buildings:
        if building.type_tag != "SAWMILL":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        if not getattr(building, "active", False):
            continue
        want = max(0, int(getattr(building, "input_capacity", lambda: 0)()) - int(getattr(building, "input_amount", lambda: 0)()))
        if want <= 0:
            continue
        count = min(want, remaining_wood)
        for _ in range(count):
            tasks.append(TransportTask(resource="wood", source=town_hall, target=building, priority=0))
        remaining_wood -= count
        if remaining_wood <= 0:
            break
    return tasks


def sawmill_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority export tasks from sawmills to Town Hall warehouse."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "SAWMILL":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "output_amount", lambda: 0)())
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="boards", source=building, target=town_hall, priority=0))
    return tasks


def _processor_accepts_resource(building: Building, resource: str) -> bool:
    add_method_name = PROCESSOR_INPUT_ADD_METHOD_BY_RESOURCE.get(str(resource))
    if add_method_name is None:
        return False
    if not callable(getattr(building, add_method_name, None)):
        return False
    if not callable(getattr(building, "input_capacity", None)):
        return False
    return callable(getattr(building, "input_amount", None))


def processor_input_transport_tasks(registry: Any, resource: str) -> list[TransportTask]:
    """Build low-priority refill tasks from Town Hall to active resource consumers."""
    if registry is None:
        return []
    resource_key = str(resource)
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None or not hasattr(town_hall, "warehouse_amount"):
        return []
    available = int(town_hall.warehouse_amount(resource_key))
    if available <= 0:
        return []
    tasks: list[TransportTask] = []
    remaining = available
    for building in buildings:
        if not _processor_accepts_resource(building, resource_key):
            continue
        if getattr(building, "is_under_construction", False):
            continue
        if not getattr(building, "active", False):
            continue
        want = max(
            0,
            int(getattr(building, "input_capacity")())
            - int(getattr(building, "input_amount")()),
        )
        if want <= 0:
            continue
        count = min(want, remaining)
        for _ in range(count):
            tasks.append(TransportTask(resource=resource_key, source=town_hall, target=building, priority=0))
        remaining -= count
        if remaining <= 0:
            break
    return tasks


def mill_input_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority refill tasks from Town Hall to active mills."""
    return processor_input_transport_tasks(registry, "wheat")


def mill_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority export tasks from mills to Town Hall warehouse."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "MILL":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "output_amount", lambda: 0)())
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="flour", source=building, target=town_hall, priority=0))
    return tasks


def bakery_input_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority flour refill tasks from Town Hall to active bakeries."""
    return processor_input_transport_tasks(registry, "flour")


def canteen_input_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority chicken and bread tasks from Town Hall to active canteens."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None or not hasattr(town_hall, "warehouse_amount"):
        return []
    remaining_chicken = int(town_hall.warehouse_amount("chicken"))
    remaining_bread = int(town_hall.warehouse_amount("bread"))
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "CANTEEN":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        if not getattr(building, "active", False):
            continue
        if remaining_chicken > 0:
            cap = int(building.local_storage_capacity("chicken"))
            amt = int(building.local_storage_amount("chicken"))
            want = max(0, cap - amt)
            count = min(want, remaining_chicken)
            for _ in range(count):
                tasks.append(TransportTask(resource="chicken", source=town_hall, target=building, priority=0))
            remaining_chicken -= count
        if remaining_bread > 0:
            cap = int(building.local_storage_capacity("bread"))
            amt = int(building.local_storage_amount("bread"))
            want = max(0, cap - amt)
            count = min(want, remaining_bread)
            for _ in range(count):
                tasks.append(TransportTask(resource="bread", source=town_hall, target=building, priority=0))
            remaining_bread -= count
    return tasks


def bakery_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority bread export tasks from bakeries to Town Hall warehouse."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "BAKERY":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "output_amount", lambda: 0)())
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="bread", source=building, target=town_hall, priority=0))
    return tasks


def chicken_farm_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority chicken export tasks from chicken farms to Town Hall warehouse."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "CHICKEN_FARM":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "output_amount", lambda: 0)())
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="chicken", source=building, target=town_hall, priority=0))
    return tasks


def _water_capacity(building: Building) -> int:
    water_capacity = getattr(building, "water_capacity", None)
    if callable(water_capacity):
        return int(water_capacity())
    return 0


def _water_amount(building: Building) -> int:
    water_amount = getattr(building, "water_amount", None)
    if callable(water_amount):
        return int(water_amount())
    return 0


def _accepts_water_input(building: Building) -> bool:
    return (
        callable(getattr(building, "water_amount", None))
        and callable(getattr(building, "water_capacity", None))
        and callable(getattr(building, "add_water_in", None))
    )


def water_input_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build direct water tasks from free wells to any active water consumer."""
    if registry is None:
        return []
    buildings = list(registry.all())
    wells = [
        b
        for b in buildings
        if b.type_tag == "WELL"
        and not getattr(b, "is_under_construction", False)
        and not bool(getattr(b, "busy", False))
    ]
    if not wells:
        return []
    tasks: list[TransportTask] = []
    well_idx = 0
    for building in buildings:
        if not _accepts_water_input(building):
            continue
        if getattr(building, "is_under_construction", False):
            continue
        if not getattr(building, "active", False):
            continue
        capacity = _water_capacity(building)
        water = _water_amount(building)
        want = max(0, capacity - water)
        for _ in range(want):
            if well_idx >= len(wells):
                return tasks
            tasks.append(TransportTask(resource="water", source=wells[well_idx], target=building, priority=0))
            well_idx += 1
    return tasks


def iron_mine_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority export tasks from iron mines to Town Hall warehouse."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "IRON_MINE":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "stored", 0))
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="iron", source=building, target=town_hall, priority=0))
    return tasks


def farm_wheat_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority wheat export tasks from farms to Town Hall."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "FARM":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "stored", 0))
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="wheat", source=building, target=town_hall, priority=0))
    return tasks
