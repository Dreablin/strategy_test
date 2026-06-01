"""Domain flow for starting the single active research run."""

from __future__ import annotations

from game.laboratory_visibility import completed_laboratory
from game.lock_reasons import lock_reason_cannot_start, lock_reason_no_laboratory
from game.research_config import RESEARCH_BY_ID
from game.research_eligibility import research_start_eligibility_for_registry
from game.research_state import ResearchState


class ResearchStartError(ValueError):
    """Raised when an ineligible research start is requested."""

    def __init__(self, message: str, *, lock_reason: str | None = None) -> None:
        super().__init__(message)
        self.lock_reason = lock_reason


def try_start_active_research(
    research_id: str,
    *,
    research_state: ResearchState,
    registry: object,
) -> None:
    """Start *research_id* when eligible; set it as the only active research."""
    eligibility = research_start_eligibility_for_registry(
        research_id,
        research_state=research_state,
        registry=registry,
    )
    if not eligibility.can_start:
        reason = eligibility.lock_reason or lock_reason_cannot_start()
        raise ResearchStartError(reason, lock_reason=eligibility.lock_reason)
    key = str(research_id)
    research_state.start_research(key)
    laboratory = completed_laboratory(registry)
    if laboratory is None:
        raise ResearchStartError(lock_reason_no_laboratory(), lock_reason=lock_reason_no_laboratory())
    definition = RESEARCH_BY_ID[key]
    laboratory.initialize_research_input_storage(definition.resource_cost)
