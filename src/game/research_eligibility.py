"""Pure rules for whether a research can be started (base gates only)."""

from __future__ import annotations

from dataclasses import dataclass

from game.laboratory_visibility import has_completed_laboratory
from game.research_config import RESEARCH_BY_ID, RESEARCH_DEFINITIONS
from game.research_state import ResearchState

_REASON_NO_LABORATORY = "Laboratory required"
_REASON_COMPLETED = "Already completed"
_REASON_ACTIVE = "Another research is in progress"


@dataclass(frozen=True, slots=True)
class ResearchStartEligibility:
    can_start: bool
    lock_reason: str | None = None


def research_start_eligibility(
    research_id: str,
    *,
    research_state: ResearchState,
    has_completed_laboratory: bool,
) -> ResearchStartEligibility:
    """Base eligibility: laboratory present, not completed, no other active research."""
    key = str(research_id)
    if key not in RESEARCH_BY_ID:
        return ResearchStartEligibility(False, f"Unknown research {key!r}")
    if not has_completed_laboratory:
        return ResearchStartEligibility(False, _REASON_NO_LABORATORY)
    if research_state.is_completed(key):
        return ResearchStartEligibility(False, _REASON_COMPLETED)
    if research_state.has_active_research():
        return ResearchStartEligibility(False, _REASON_ACTIVE)
    return ResearchStartEligibility(True, None)


def research_start_eligibility_for_registry(
    research_id: str,
    *,
    research_state: ResearchState,
    registry: object,
) -> ResearchStartEligibility:
    return research_start_eligibility(
        research_id,
        research_state=research_state,
        has_completed_laboratory=has_completed_laboratory(registry),
    )


def research_can_start_map(
    *,
    research_state: ResearchState,
    has_completed_laboratory: bool,
) -> dict[str, bool]:
    return {
        entry.id: research_start_eligibility(
            entry.id,
            research_state=research_state,
            has_completed_laboratory=has_completed_laboratory,
        ).can_start
        for entry in RESEARCH_DEFINITIONS
    }


def research_lock_reasons(
    *,
    research_state: ResearchState,
    has_completed_laboratory: bool,
) -> dict[str, str]:
    reasons: dict[str, str] = {}
    for entry in RESEARCH_DEFINITIONS:
        result = research_start_eligibility(
            entry.id,
            research_state=research_state,
            has_completed_laboratory=has_completed_laboratory,
        )
        if result.lock_reason:
            reasons[entry.id] = result.lock_reason
    return reasons
