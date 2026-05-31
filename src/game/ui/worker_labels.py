"""Shared worker display labels for UI panels."""

from __future__ import annotations

from game import i18n
from game.worker_hiring import HIRABLE_WORKERS, worker_compatible_building_types


def worker_display_label(worker_type: str) -> str:
    key = str(worker_type).upper()
    locale_key = f"worker.{key}"
    label = i18n.t(locale_key)
    if label != locale_key:
        return label
    return key.replace("_", " ").title()


def building_worker_display_label(building_type: str) -> str | None:
    tag = str(building_type).upper()
    for worker_type in sorted(HIRABLE_WORKERS, key=worker_display_label):
        if tag in worker_compatible_building_types(worker_type):
            return worker_display_label(worker_type)
    return None


def building_worker_status_line(building_type: str, worker_status: str) -> str:
    label = building_worker_display_label(building_type)
    worker_word = i18n.t("ui.common.worker")
    if label is None:
        return f"{worker_word}: {worker_status}"
    return f"{worker_word} ({label}): {worker_status}"
