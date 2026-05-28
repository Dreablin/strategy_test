"""Completed research effects applied to worker characteristics."""

from __future__ import annotations

from collections.abc import Iterable

from game.research_config import RESEARCH_DEFINITIONS, RESEARCH_BY_ID


def research_worker_effect_source(research_id: str, worker_type: str) -> tuple[str, str, str]:
    return ("research", str(research_id), str(worker_type).upper())


def research_worker_effect_source_keys(worker_type: str) -> tuple[tuple[str, str, str], ...]:
    type_key = str(worker_type).upper()
    return tuple(
        research_worker_effect_source(definition.id, type_key)
        for definition in RESEARCH_DEFINITIONS
        if type_key in definition.worker_effects_by_type
    )


def completed_research_worker_effect_sources(
    completed_ids: Iterable[str],
    worker_type: str,
) -> list[tuple[tuple[str, str, str], dict[str, float]]]:
    type_key = str(worker_type).upper()
    result: list[tuple[tuple[str, str, str], dict[str, float]]] = []
    for research_id in sorted(str(value) for value in completed_ids):
        definition = RESEARCH_BY_ID.get(research_id)
        if definition is None:
            continue
        effects = definition.worker_effects_by_type.get(type_key, {})
        if effects:
            result.append((research_worker_effect_source(research_id, type_key), effects))
    return result
