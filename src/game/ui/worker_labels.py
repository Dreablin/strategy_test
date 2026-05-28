"""Shared worker display labels for UI panels."""

from __future__ import annotations

from game.worker_hiring import HIRABLE_WORKERS, worker_compatible_building_types

WORKER_LABEL: dict[str, str] = {
    "CARRIER": "Carrier",
    "BUILDER": "Builder",
    "SAWYER": "Sawyer",
    "MILLER": "Miller",
    "BAKER": "Baker",
    "COOK": "Cook",
    "WATERMAN": "Waterman",
    "LUMBERJACK": "Lumberjack",
    "STONECUTTER": "Stonecutter",
    "MINER": "Miner",
    "FARMER": "Farmer",
    "ANIMAL_HERDER": "Herder",
    "FORESTER": "Forester",
    "WINEMAKER": "Winemaker",
    "SCIENTIST": "Scientist",
}


def worker_display_label(worker_type: str) -> str:
    key = str(worker_type).upper()
    return WORKER_LABEL.get(key, key.replace("_", " ").title())


def building_worker_display_label(building_type: str) -> str | None:
    tag = str(building_type).upper()
    for worker_type in sorted(HIRABLE_WORKERS, key=worker_display_label):
        if tag in worker_compatible_building_types(worker_type):
            return worker_display_label(worker_type)
    return None


def building_worker_status_line(building_type: str, worker_status: str) -> str:
    label = building_worker_display_label(building_type)
    if label is None:
        return f"Worker: {worker_status}"
    return f"Worker ({label}): {worker_status}"
