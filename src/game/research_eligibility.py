"""Pure rules for whether a research can be started."""

from __future__ import annotations

from dataclasses import dataclass

from game.buildings.laboratory import Laboratory
from game.laboratory_visibility import has_completed_laboratory
from game.research_config import RESEARCH_BY_ID, RESEARCH_DEFINITIONS
from game.research_state import ResearchState

_LABORATORY_TAG = "LABORATORY"
_REASON_NO_LABORATORY = "Laboratory required"
_REASON_COMPLETED = "Already completed"
_REASON_ACTIVE = "Another research is in progress"


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
    if laboratory_level is not None:
        definition = RESEARCH_BY_ID[key]
        lab = Laboratory(level=laboratory_level)
        if not lab.unlocks_technology_tier(definition.tier):
            required = lab.technology_tier_unlock_level(definition.tier)
            return ResearchStartEligibility(False, _tier_lock_reason(required))
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
