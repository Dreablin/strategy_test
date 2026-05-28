"""Technology tier chain unlock rules (completion + Laboratory level)."""

from __future__ import annotations

from game.research_config import RESEARCH_BY_ID
from game.research_eligibility import (
    ResearchStartEligibility,
    missing_research_dependencies,
    research_start_eligibility_for_registry,
)
from game.research_state import ResearchState

TECHNOLOGY_IDS: tuple[str, ...] = ("1", "2", "3", "4")


def next_technology_id(research_id: str) -> str | None:
    """The next Technology id in the static chain, if any."""
    key = str(research_id)
    if key not in TECHNOLOGY_IDS:
        return None
    index = TECHNOLOGY_IDS.index(key)
    if index + 1 >= len(TECHNOLOGY_IDS):
        return None
    return TECHNOLOGY_IDS[index + 1]


def technology_chain_prerequisite_met(
    research_id: str,
    *,
    research_state: ResearchState,
) -> bool:
    """Whether configured Technology dependencies are satisfied."""
    if str(research_id) not in RESEARCH_BY_ID:
        return False
    return not missing_research_dependencies(str(research_id), research_state=research_state)


def technology_start_eligibility(
    research_id: str,
    *,
    research_state: ResearchState,
    registry: object,
) -> ResearchStartEligibility:
    """Start eligibility for a Technology research (chain + Laboratory tier gates)."""
    return research_start_eligibility_for_registry(
        str(research_id),
        research_state=research_state,
        registry=registry,
    )


def technologies_unlocked_for_start(
    *,
    research_state: ResearchState,
    registry: object,
) -> tuple[str, ...]:
    """Technology ids that can be started now under chain and Laboratory rules."""
    return tuple(
        tech_id
        for tech_id in TECHNOLOGY_IDS
        if technology_start_eligibility(
            tech_id,
            research_state=research_state,
            registry=registry,
        ).can_start
    )


def technology_unlocked_after_completing(
    completed_id: str,
    *,
    research_state: ResearchState,
    registry: object,
) -> str | None:
    """Next Technology in the chain that becomes startable after *completed_id*, if any."""
    next_id = next_technology_id(completed_id)
    if next_id is None:
        return None
    result = technology_start_eligibility(
        next_id,
        research_state=research_state,
        registry=registry,
    )
    return next_id if result.can_start else None
