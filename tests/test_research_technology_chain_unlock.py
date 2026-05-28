"""Technology chain unlock via completion and Laboratory tier gates (T432)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_completion import try_complete_active_research
from game.research_config import RESEARCH_BY_ID
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.research_technology_chain import (
    TECHNOLOGY_IDS,
    technologies_unlocked_for_start,
    technology_start_eligibility,
    technology_unlocked_after_completing,
)
from game.world import World


def _registry(*, laboratory_level: int) -> tuple[BuildingRegistry, Laboratory]:
    world = World(world_seed=50)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = laboratory_level
    laboratory.construction_site = None
    return registry, laboratory


def _complete_technology(
    state: ResearchState,
    laboratory: Laboratory,
    registry: BuildingRegistry,
    tech_id: str,
) -> None:
    definition = RESEARCH_BY_ID[tech_id]
    try_start_active_research(tech_id, research_state=state, registry=registry)
    for resource, amount in definition.resource_cost.items():
        state.add_delivered(resource, amount)
    state.add_points(definition.required_points)
    assert try_complete_active_research(research_state=state, laboratory=laboratory)


def test_technology_ids_match_configured_chain() -> None:
    assert TECHNOLOGY_IDS == ("1", "2", "3", "4")
    for index, tech_id in enumerate(TECHNOLOGY_IDS):
        assert RESEARCH_BY_ID[tech_id].tier == index + 1
        if index == 0:
            assert RESEARCH_BY_ID[tech_id].dependencies == ()
        else:
            assert RESEARCH_BY_ID[tech_id].dependencies == (TECHNOLOGY_IDS[index - 1],)


def test_completing_technology_1_unlocks_2_only_when_laboratory_level_permits() -> None:
    registry, laboratory = _registry(laboratory_level=1)
    state = ResearchState()
    _complete_technology(state, laboratory, registry, "1")
    assert technology_unlocked_after_completing(
        "1", research_state=state, registry=registry
    ) is None
    blocked = technology_start_eligibility("2", research_state=state, registry=registry)
    assert blocked.can_start is False
    assert blocked.lock_reason == "Requires Laboratory level 3"

    registry, laboratory = _registry(laboratory_level=3)
    state = ResearchState()
    _complete_technology(state, laboratory, registry, "1")
    assert technology_unlocked_after_completing(
        "1", research_state=state, registry=registry
    ) == "2"
    assert technologies_unlocked_for_start(research_state=state, registry=registry) == ("2",)


def test_completing_chain_through_technology_3_at_level_6() -> None:
    registry, laboratory = _registry(laboratory_level=6)
    state = ResearchState()
    _complete_technology(state, laboratory, registry, "1")
    _complete_technology(state, laboratory, registry, "2")
    assert technology_unlocked_after_completing(
        "2", research_state=state, registry=registry
    ) == "3"
    assert technologies_unlocked_for_start(research_state=state, registry=registry) == ("3",)
    blocked = technology_start_eligibility("4", research_state=state, registry=registry)
    assert blocked.can_start is False
    assert blocked.lock_reason == "Requires Laboratory level 9"


def test_full_technology_chain_unlocks_through_level_9() -> None:
    registry, laboratory = _registry(laboratory_level=9)
    state = ResearchState()
    for tech_id in ("1", "2", "3"):
        _complete_technology(state, laboratory, registry, tech_id)
    assert technology_unlocked_after_completing(
        "3", research_state=state, registry=registry
    ) == "4"
    assert technologies_unlocked_for_start(research_state=state, registry=registry) == ("4",)
    _complete_technology(state, laboratory, registry, "4")
    assert technologies_unlocked_for_start(research_state=state, registry=registry) == ()
    for tech_id in TECHNOLOGY_IDS:
        assert state.is_completed(tech_id)
