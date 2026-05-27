"""Research domain state tests (T389)."""

from __future__ import annotations

import pytest

from game.research_config import RESEARCH_BY_ID
from game.research_state import ResearchState


def test_initial_state_is_empty() -> None:
    state = ResearchState()
    assert state.completed_ids() == frozenset()
    assert state.active_research_id() is None
    assert state.delivered_amounts() == {}
    assert state.accumulated_points() == 0
    assert not state.has_active_research()


def test_start_research_initializes_delivery_tracking() -> None:
    state = ResearchState()
    state.start_research("1")
    definition = RESEARCH_BY_ID["1"]
    assert state.active_research_id() == "1"
    assert state.has_active_research()
    assert state.accumulated_points() == 0
    assert set(state.delivered_amounts()) == set(definition.resource_cost)
    assert all(amount == 0 for amount in state.delivered_amounts().values())


def test_start_research_rejects_unknown_completed_or_second_active() -> None:
    state = ResearchState()
    with pytest.raises(ValueError, match="unknown research"):
        state.start_research("missing")
    state.start_research("1")
    with pytest.raises(ValueError, match="already active"):
        state.start_research("2")
    state.mark_research_completed("1")
    with pytest.raises(ValueError, match="already completed"):
        state.start_research("1")


def test_mark_research_completed_updates_completed_and_clears_active() -> None:
    state = ResearchState()
    state.start_research("1")
    definition = RESEARCH_BY_ID["1"]
    for resource, required in definition.resource_cost.items():
        state.add_delivered(resource, required)
    state.add_points(100)
    state.mark_research_completed("1")
    assert state.is_completed("1")
    assert "1" in state.completed_ids()
    assert state.active_research_id() is None
    assert state.delivered_amounts() == {}
    assert state.accumulated_points() == 0


def test_mark_completed_requires_active_match() -> None:
    state = ResearchState()
    state.start_research("1")
    with pytest.raises(ValueError, match="not the active research"):
        state.mark_research_completed("2")


def test_delivered_and_points_bookkeeping() -> None:
    state = ResearchState()
    state.start_research("1")
    wood_cap = RESEARCH_BY_ID["1"].resource_cost["wood"]
    state.add_delivered("wood", 3)
    state.add_delivered("wood", 10)
    assert state.delivered_amounts()["wood"] == 13
    state.add_delivered("wood", wood_cap)
    assert state.delivered_amounts()["wood"] == wood_cap
    boards_cap = RESEARCH_BY_ID["1"].resource_cost["boards"]
    state.add_delivered("boards", boards_cap)
    assert state.all_resources_delivered()
    state.add_points(250)
    state.add_points(100)
    assert state.accumulated_points() == 350


def test_delivered_requires_active_research_and_valid_resource() -> None:
    state = ResearchState()
    with pytest.raises(ValueError, match="no active research"):
        state.add_delivered("wood", 1)
    state.start_research("1")
    with pytest.raises(ValueError, match="not required"):
        state.add_delivered("wine", 1)
    state.add_delivered("wood", RESEARCH_BY_ID["1"].resource_cost["wood"])
    state.add_delivered("boards", RESEARCH_BY_ID["1"].resource_cost["boards"])
    with pytest.raises(ValueError, match="fully delivered"):
        state.add_delivered("wood", 1)


def test_points_require_active_research() -> None:
    state = ResearchState()
    with pytest.raises(ValueError, match="no active research"):
        state.add_points(1)
    with pytest.raises(ValueError, match="non-negative"):
        state.start_research("1")
        state.add_points(-1)
