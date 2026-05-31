"""Defensive research config validity checks in eligibility (T418)."""

from __future__ import annotations

from unittest.mock import patch

from game.lock_reasons import lock_reason_invalid_cost, lock_reason_invalid_points
from game.research_config import RESEARCH_BY_ID, ResearchDefinition
from game.research_eligibility import (
    research_config_lock_reason,
    research_start_eligibility,
)
from game.research_state import ResearchState


def _sample_definition(
    *,
    resource_cost: dict[str, int] | None = None,
    required_points: int = 100,
    research_id: str = "sample",
) -> ResearchDefinition:
    return ResearchDefinition(
        id=research_id,
        name="Sample",
        description="Sample research",
        effect_text="Sample effect",
        tier=1,
        column=1,
        dependencies=(),
        resource_cost={"wood": 1} if resource_cost is None else resource_cost,
        required_points=required_points,
        image_key="technology_1",
    )


def test_valid_definition_has_no_lock_reason() -> None:
    assert research_config_lock_reason(_sample_definition()) is None
    assert research_config_lock_reason(RESEARCH_BY_ID["1"]) is None


def test_empty_resource_cost_is_not_startable() -> None:
    bad = _sample_definition(resource_cost={})
    assert research_config_lock_reason(bad) == lock_reason_invalid_cost()


def test_non_positive_point_requirement_is_not_startable() -> None:
    bad = _sample_definition(required_points=0)
    assert research_config_lock_reason(bad) == lock_reason_invalid_points()


def test_non_positive_resource_amount_is_not_startable() -> None:
    bad = _sample_definition(resource_cost={"wood": 0})
    assert research_config_lock_reason(bad) == lock_reason_invalid_cost()


def test_eligibility_uses_config_lock_reason_for_invalid_entry() -> None:
    bad = _sample_definition(resource_cost={}, research_id="invalid_cost")
    state = ResearchState()
    with patch.dict(RESEARCH_BY_ID, {"invalid_cost": bad}, clear=False):
        result = research_start_eligibility(
            "invalid_cost",
            research_state=state,
            has_completed_laboratory=True,
            laboratory_level=10,
        )
    assert result.can_start is False
    assert result.lock_reason == "Research resource cost is not configured"
