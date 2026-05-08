"""Canteen diner slot reservations (independent of local meal storage)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.worker_models import Worker


def count_reserved_diner_slots(canteen: Canteen) -> int:
    return len(canteen._diner_occupants)


def count_reserved_meals(canteen: Canteen) -> int:
    return len(canteen._reserved_meal_workers)


def available_meals_for_reservation(canteen: Canteen) -> int:
    return max(0, int(canteen.local_storage_amount("simple_meal")) - count_reserved_meals(canteen))


def try_reserve_diner_slot(canteen: Canteen, worker: Worker) -> bool:
    if worker.dining_canteen is not None:
        return False
    if worker in canteen._diner_occupants:
        return False
    if len(canteen._diner_occupants) >= canteen.diner_slot_capacity():
        return False
    canteen._diner_occupants.add(worker)
    worker.dining_canteen = canteen
    return True


def try_reserve_diner_slot_and_meal(canteen: Canteen, worker: Worker) -> bool:
    if available_meals_for_reservation(canteen) <= 0:
        return False
    if not try_reserve_diner_slot(canteen, worker):
        return False
    canteen._reserved_meal_workers.add(worker)
    worker.dining_meal_reserved = True
    return True


def release_reserved_meal(canteen: Canteen, worker: Worker) -> None:
    canteen._reserved_meal_workers.discard(worker)
    worker.dining_meal_reserved = False


def release_diner_slot_after_meal(canteen: Canteen, worker: Worker) -> None:
    if worker not in canteen._diner_occupants:
        return
    canteen._diner_occupants.discard(worker)
    release_reserved_meal(canteen, worker)
    worker.dining_queue_order = -1
    if worker.dining_canteen is canteen:
        worker.dining_canteen = None


def release_diner_slots_for_worker(worker: Worker) -> None:
    canteen = worker.dining_canteen
    if canteen is None:
        return
    if isinstance(canteen, Canteen):
        canteen._diner_occupants.discard(worker)
        release_reserved_meal(canteen, worker)
    else:
        worker.dining_meal_reserved = False
    worker.dining_queue_order = -1
    worker.dining_canteen = None


def release_all_diner_slots_for_canteen(canteen: Canteen) -> None:
    for worker in list(canteen._diner_occupants):
        if worker.dining_canteen is canteen:
            worker.dining_canteen = None
        release_reserved_meal(canteen, worker)
        worker.dining_queue_order = -1
    canteen._diner_occupants.clear()
    canteen._reserved_meal_workers.clear()
