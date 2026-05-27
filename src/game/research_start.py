"""Domain flow for starting the single active research run."""

from __future__ import annotations

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
        reason = eligibility.lock_reason or "Research cannot be started"
        raise ResearchStartError(reason, lock_reason=eligibility.lock_reason)
    research_state.start_research(research_id)
