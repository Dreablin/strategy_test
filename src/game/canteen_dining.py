"""Diner slot reservations for dining buildings (Canteen, Restaurant, etc.)."""

from __future__ import annotations

from typing import Any

from game.worker_models import Worker


def count_reserved_diner_slots(building: Any) -> int:
    return len(building._diner_occupants)


def count_reserved_meals(building: Any) -> int:
    return len(building._reserved_meal_workers)


def available_meals_for_reservation(building: Any) -> int:
    meal_key = str(building.meal_resource_key())
    return max(0, int(building.local_storage_amount(meal_key)) - count_reserved_meals(building))


def try_reserve_diner_slot(building: Any, worker: Worker) -> bool:
    if worker.dining_canteen is not None:
        return False
    if worker in building._diner_occupants:
        return False
    if len(building._diner_occupants) >= building.diner_slot_capacity():
        return False
    building._diner_occupants.add(worker)
    worker.dining_canteen = building
    return True


def try_reserve_diner_slot_and_meal(building: Any, worker: Worker) -> bool:
    if available_meals_for_reservation(building) <= 0:
        return False
    if not try_reserve_diner_slot(building, worker):
        return False
    building._reserved_meal_workers.add(worker)
    worker.dining_meal_reserved = True
    return True


def release_reserved_meal(building: Any, worker: Worker) -> None:
    building._reserved_meal_workers.discard(worker)
    worker.dining_meal_reserved = False


def release_diner_slot_after_meal(building: Any, worker: Worker) -> None:
    if worker not in building._diner_occupants:
        return
    building._diner_occupants.discard(worker)
    release_reserved_meal(building, worker)
    worker.dining_queue_order = -1
    if worker.dining_canteen is building:
        worker.dining_canteen = None


def release_diner_slots_for_worker(worker: Worker) -> None:
    building = worker.dining_canteen
    if building is None:
        return
    if hasattr(building, "_diner_occupants"):
        building._diner_occupants.discard(worker)
        release_reserved_meal(building, worker)
    else:
        worker.dining_meal_reserved = False
    worker.dining_queue_order = -1
    worker.dining_canteen = None


def release_all_diner_slots_for_building(building: Any) -> None:
    for worker in list(building._diner_occupants):
        if worker.dining_canteen is building:
            worker.dining_canteen = None
        release_reserved_meal(building, worker)
        worker.dining_queue_order = -1
    building._diner_occupants.clear()
    building._reserved_meal_workers.clear()


# Keep old name as alias for backwards compatibility
release_all_diner_slots_for_canteen = release_all_diner_slots_for_building
