"""Base research start eligibility tests (T415)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.laboratory_visibility import has_completed_laboratory
from game.research_eligibility import (
    research_can_start_map,
    research_lock_reasons,
    research_start_eligibility,
    research_start_eligibility_for_registry,
)
from game.research_state import ResearchState
from game.world import World


def _registry(*, laboratory_completed: bool) -> BuildingRegistry:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    if laboratory_completed:
        laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
        laboratory.construction_site = None
    return registry


def test_requires_completed_laboratory() -> None:
    state = ResearchState()
    result = research_start_eligibility("1", research_state=state, has_completed_laboratory=False)
    assert result.can_start is False
    assert result.lock_reason == "Laboratory required"


def test_eligible_when_laboratory_exists_and_no_blockers() -> None:
    state = ResearchState()
    result = research_start_eligibility("1", research_state=state, has_completed_laboratory=True)
    assert result.can_start is True
    assert result.lock_reason is None


def test_completed_research_cannot_start() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    result = research_start_eligibility("1", research_state=state, has_completed_laboratory=True)
    assert result.can_start is False
    assert result.lock_reason == "Already completed"


def test_active_research_blocks_all_starts() -> None:
    state = ResearchState()
    state.start_research("1")
    for research_id in ("1", "2", "3", "4"):
        result = research_start_eligibility(
            research_id,
            research_state=state,
            has_completed_laboratory=True,
        )
        assert result.can_start is False
        assert result.lock_reason == "Another research is in progress"


def test_registry_helper_uses_laboratory_presence() -> None:
    state = ResearchState()
    without = _registry(laboratory_completed=False)
    with_lab = _registry(laboratory_completed=True)
    assert research_start_eligibility_for_registry(
        "1", research_state=state, registry=without
    ).can_start is False
    assert research_start_eligibility_for_registry(
        "1", research_state=state, registry=with_lab
    ).can_start is True
    assert has_completed_laboratory(with_lab) is True


def test_lock_reasons_and_can_start_map() -> None:
    state = ResearchState()
    state.start_research("1")
    reasons = research_lock_reasons(research_state=state, has_completed_laboratory=True)
    assert reasons["1"] == "Another research is in progress"
    assert reasons["2"] == "Another research is in progress"
    can_start = research_can_start_map(research_state=state, has_completed_laboratory=True)
    assert can_start["1"] is False
    assert all(not allowed for allowed in can_start.values())
