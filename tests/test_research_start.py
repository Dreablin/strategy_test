"""Domain start-active-research behavior tests (T420)."""

from __future__ import annotations

import pytest

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.lock_reasons import (
    lock_reason_active_research,
    lock_reason_requires_laboratory_level,
)
from game.research_config import RESEARCH_BY_ID
from game.research_start import ResearchStartError, try_start_active_research
from game.research_state import ResearchState
from game.world import World


def _registry(*, laboratory_level: int = 1) -> BuildingRegistry:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    laboratory.level = laboratory_level
    return registry


def test_try_start_sets_active_research_id() -> None:
    state = ResearchState()
    registry = _registry()
    try_start_active_research("1", research_state=state, registry=registry)
    assert state.active_research_id() == "1"
    assert state.has_active_research()


def test_try_start_rejects_ineligible_research(use_locale) -> None:
    state = ResearchState()
    registry = _registry(laboratory_level=1)
    with use_locale("en"):
        with pytest.raises(ResearchStartError, match="Laboratory level 3") as exc:
            try_start_active_research("2", research_state=state, registry=registry)
        assert exc.value.lock_reason == lock_reason_requires_laboratory_level(3)
    assert state.active_research_id() is None


def test_try_start_rejects_second_active_research(use_locale) -> None:
    state = ResearchState()
    registry = _registry(laboratory_level=10)
    with use_locale("en"):
        try_start_active_research("1", research_state=state, registry=registry)
        with pytest.raises(ResearchStartError, match="in progress") as exc:
            try_start_active_research("2", research_state=state, registry=registry)
        assert exc.value.lock_reason == lock_reason_active_research()
    assert state.active_research_id() == "1"


def test_try_start_rejects_completed_research(use_locale) -> None:
    state = ResearchState()
    registry = _registry(laboratory_level=10)
    with use_locale("en"):
        try_start_active_research("1", research_state=state, registry=registry)
        state.mark_research_completed("1")
        with pytest.raises(ResearchStartError, match="Already completed"):
            try_start_active_research("1", research_state=state, registry=registry)
    assert state.active_research_id() is None


def test_failed_start_does_not_initialize_laboratory_input_storage() -> None:
    state = ResearchState()
    registry = _registry(laboratory_level=1)
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    with pytest.raises(ResearchStartError):
        try_start_active_research("2", research_state=state, registry=registry)
    assert not laboratory.has_research_input_storage()


def test_try_start_initializes_laboratory_input_storage_from_cost_map() -> None:
    state = ResearchState()
    registry = _registry()
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    definition = RESEARCH_BY_ID["1"]
    try_start_active_research("1", research_state=state, registry=registry)
    assert laboratory.has_research_input_storage()
    assert set(laboratory.research_input_resources()) == set(definition.resource_cost)
    for resource, capacity in definition.resource_cost.items():
        assert laboratory.research_input_capacity(resource) == capacity
        assert laboratory.research_input_amount(resource) == 0


def test_laboratory_storage_reinitialized_for_new_research_cost_shape() -> None:
    state = ResearchState()
    registry = _registry(laboratory_level=10)
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    try_start_active_research("1", research_state=state, registry=registry)
    state.mark_research_completed("1")
    try_start_active_research("2", research_state=state, registry=registry)
    definition = RESEARCH_BY_ID["2"]
    assert set(laboratory.research_input_resources()) == set(definition.resource_cost)
    assert laboratory.research_input_amount("boards") == 0
    assert laboratory.research_input_capacity("boards") == definition.resource_cost["boards"]
