"""Pure rules for whether a research can be started."""

from __future__ import annotations

from dataclasses import dataclass

from game.buildings.laboratory import Laboratory
from game.laboratory_visibility import has_completed_laboratory
from game.research_config import RESEARCH_BY_ID, RESEARCH_DEFINITIONS, ResearchDefinition
from game.research_state import ResearchState

_LABORATORY_TAG = "LABORATORY"
_REASON_NO_LABORATORY = "Laboratory required"
_REASON_COMPLETED = "Already completed"
_REASON_ACTIVE = "Another research is in progress"
_REASON_INVALID_COST = "Research resource cost is not configured"
_REASON_INVALID_POINTS = "Research point requirement is invalid"


def _dependency_lock_reason(missing_dependency_ids: tuple[str, ...]) -> str:
    names = [RESEARCH_BY_ID[dep_id].name for dep_id in missing_dependency_ids]
    if len(names) == 1:
        return f"Requires {names[0]}"
    return "Requires " + ", ".join(names)


def research_config_lock_reason(definition: ResearchDefinition) -> str | None:
    """Defensive validity check for cost shape and point requirement."""
    if definition.required_points <= 0:
        return _REASON_INVALID_POINTS
    if not definition.resource_cost:
        return _REASON_INVALID_COST
    for resource, amount in definition.resource_cost.items():
        if not str(resource).strip():
            return _REASON_INVALID_COST
        if amount <= 0:
            return _REASON_INVALID_COST
    return None


def missing_research_dependencies(
    research_id: str,
    *,
    research_state: ResearchState,
) -> tuple[str, ...]:
    """Dependency ids from config that are not yet completed."""
    definition = RESEARCH_BY_ID[str(research_id)]
    return tuple(dep for dep in definition.dependencies if not research_state.is_completed(dep))


@dataclass(frozen=True, slots=True)
class ResearchStartEligibility:
    can_start: bool
    lock_reason: str | None = None


def completed_laboratory_level(registry: object) -> int | None:
    """Level of the built Laboratory, or ``None`` if none is complete."""
    buildings = getattr(registry, "all", None)
    if not callable(buildings):
        return None
    for building in buildings():
        if building.type_tag == _LABORATORY_TAG and not building.is_under_construction:
            return int(building.level)
    return None


def _tier_lock_reason(required_level: int) -> str:
    return f"Requires Laboratory level {required_level}"


def laboratory_unlocks_research_tier(laboratory_level: int, research_tier: int) -> bool:
    """Whether a Laboratory at ``laboratory_level`` unlocks researches in ``research_tier``."""
    return Laboratory(level=laboratory_level).unlocks_technology_tier(research_tier)


def research_start_eligibility(
    research_id: str,
    *,
    research_state: ResearchState,
    has_completed_laboratory: bool,
    laboratory_level: int | None = None,
) -> ResearchStartEligibility:
    """Eligibility including base gates and Laboratory tier unlock level."""
    key = str(research_id)
    if key not in RESEARCH_BY_ID:
        return ResearchStartEligibility(False, f"Unknown research {key!r}")
    if not has_completed_laboratory:
        return ResearchStartEligibility(False, _REASON_NO_LABORATORY)
    if research_state.is_completed(key):
        return ResearchStartEligibility(False, _REASON_COMPLETED)
    if research_state.has_active_research():
        return ResearchStartEligibility(False, _REASON_ACTIVE)
    definition = RESEARCH_BY_ID[key]
    config_reason = research_config_lock_reason(definition)
    if config_reason is not None:
        return ResearchStartEligibility(False, config_reason)
    if laboratory_level is not None:
        lab = Laboratory(level=laboratory_level)
        if not lab.unlocks_technology_tier(definition.tier):
            required = lab.technology_tier_unlock_level(definition.tier)
            return ResearchStartEligibility(False, _tier_lock_reason(required))
    missing_deps = missing_research_dependencies(key, research_state=research_state)
    if missing_deps:
        return ResearchStartEligibility(False, _dependency_lock_reason(missing_deps))
    return ResearchStartEligibility(True, None)


def research_start_eligibility_for_registry(
    research_id: str,
    *,
    research_state: ResearchState,
    registry: object,
) -> ResearchStartEligibility:
    has_lab = has_completed_laboratory(registry)
    level = completed_laboratory_level(registry) if has_lab else None
    return research_start_eligibility(
        research_id,
        research_state=research_state,
        has_completed_laboratory=has_lab,
        laboratory_level=level,
    )


def research_can_start_map(
    *,
    research_state: ResearchState,
    has_completed_laboratory: bool,
    laboratory_level: int | None = None,
) -> dict[str, bool]:
    return {
        entry.id: research_start_eligibility(
            entry.id,
            research_state=research_state,
            has_completed_laboratory=has_completed_laboratory,
            laboratory_level=laboratory_level,
        ).can_start
        for entry in RESEARCH_DEFINITIONS
    }


def research_lock_reasons(
    *,
    research_state: ResearchState,
    has_completed_laboratory: bool,
    laboratory_level: int | None = None,
) -> dict[str, str]:
    reasons: dict[str, str] = {}
    for entry in RESEARCH_DEFINITIONS:
        result = research_start_eligibility(
            entry.id,
            research_state=research_state,
            has_completed_laboratory=has_completed_laboratory,
            laboratory_level=laboratory_level,
        )
        if result.lock_reason:
            reasons[entry.id] = result.lock_reason
    return reasons


def research_ui_eligibility(
    *,
    research_state: ResearchState,
    registry: object,
) -> tuple[dict[str, bool], dict[str, str]]:
    """Start-button flags and tooltip lock reasons for the Research screen."""
    has_lab = has_completed_laboratory(registry)
    level = completed_laboratory_level(registry) if has_lab else None
    kwargs = {
        "research_state": research_state,
        "has_completed_laboratory": has_lab,
        "laboratory_level": level,
    }
    return research_can_start_map(**kwargs), research_lock_reasons(**kwargs)
