"""Localized lock and requirement messages for eligibility and UI."""

from __future__ import annotations

from game import i18n
from game.research_config import RESEARCH_BY_ID


def lock_reason_no_laboratory() -> str:
    return i18n.t("ui.lock.no_laboratory")


def lock_reason_already_completed() -> str:
    return i18n.t("ui.lock.already_completed")


def lock_reason_active_research() -> str:
    return i18n.t("ui.lock.active_research")


def lock_reason_invalid_cost() -> str:
    return i18n.t("ui.lock.invalid_cost")


def lock_reason_invalid_points() -> str:
    return i18n.t("ui.lock.invalid_points")


def lock_reason_requires_laboratory_level(level: int) -> str:
    return i18n.t("ui.lock.requires_laboratory_level", level=int(level))


def lock_reason_requires_research(missing_dependency_ids: tuple[str, ...]) -> str:
    names = [
        i18n.t(f"research.{dep_id}.name")
        for dep_id in missing_dependency_ids
        if dep_id in RESEARCH_BY_ID
    ]
    if len(names) == 1:
        return i18n.t("ui.lock.requires_research_one", name=names[0])
    return i18n.t("ui.lock.requires_research_many", names=", ".join(names))


def lock_reason_unknown_research(research_id: str) -> str:
    return i18n.t("ui.lock.unknown_research", id=research_id)


def lock_reason_cannot_start() -> str:
    return i18n.t("ui.lock.cannot_start")
