"""Base research start eligibility tests (T415)."""

from __future__ import annotations

from game import i18n
from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.laboratory_visibility import has_completed_laboratory
from game.lock_reasons import (
    lock_reason_active_research,
    lock_reason_already_completed,
    lock_reason_no_laboratory,
    lock_reason_requires_laboratory_level,
    lock_reason_requires_research,
)
from game.research_eligibility import (
    research_can_start_map,
    research_lock_reasons,
    research_start_eligibility,
    research_start_eligibility_for_registry,
)
from game.research_config import RESEARCH_BY_ID
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
    assert result.lock_reason == lock_reason_no_laboratory()


def test_eligible_when_laboratory_exists_and_no_blockers() -> None:
    state = ResearchState()
    result = research_start_eligibility(
        "1",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=1,
    )
    assert result.can_start is True
    assert result.lock_reason is None


def test_completed_research_cannot_start() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    result = research_start_eligibility(
        "1",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=1,
    )
    assert result.can_start is False
    assert result.lock_reason == lock_reason_already_completed()


def test_active_research_blocks_all_starts() -> None:
    state = ResearchState()
    state.start_research("1")
    for research_id in ("1", "2", "3", "4"):
        result = research_start_eligibility(
            research_id,
            research_state=state,
            has_completed_laboratory=True,
            laboratory_level=10,
        )
        assert result.can_start is False
        assert result.lock_reason == lock_reason_active_research()


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
    reasons = research_lock_reasons(
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=10,
    )
    assert reasons["1"] == lock_reason_active_research()
    assert reasons["2"] == lock_reason_active_research()
    can_start = research_can_start_map(
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=10,
    )
    assert can_start["1"] is False
    assert all(not allowed for allowed in can_start.values())


def test_tier_gates_at_laboratory_level_1() -> None:
    state = ResearchState()
    assert research_start_eligibility(
        "1", research_state=state, has_completed_laboratory=True, laboratory_level=1
    ).can_start
    blocked = research_start_eligibility(
        "2", research_state=state, has_completed_laboratory=True, laboratory_level=1
    )
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_laboratory_level(3)


def test_tier_gates_at_laboratory_level_3() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    assert research_start_eligibility(
        "2", research_state=state, has_completed_laboratory=True, laboratory_level=3
    ).can_start
    blocked = research_start_eligibility(
        "3", research_state=state, has_completed_laboratory=True, laboratory_level=3
    )
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_laboratory_level(6)


def test_tier_gates_at_laboratory_level_6() -> None:
    state = ResearchState()
    for research_id in ("1", "2"):
        state.start_research(research_id)
        state.mark_research_completed(research_id)
    assert research_start_eligibility(
        "3", research_state=state, has_completed_laboratory=True, laboratory_level=6
    ).can_start
    blocked = research_start_eligibility(
        "4", research_state=state, has_completed_laboratory=True, laboratory_level=6
    )
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_laboratory_level(9)


def test_tier_gates_at_laboratory_level_9() -> None:
    state = ResearchState()
    for research_id in ("1", "2", "3"):
        state.start_research(research_id)
        state.mark_research_completed(research_id)
    assert research_start_eligibility(
        "4",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=9,
    ).can_start


def test_registry_tier_gate_uses_placed_laboratory_level() -> None:
    state = ResearchState()
    registry = _registry(laboratory_completed=True)
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    assert laboratory.level == 1
    assert research_start_eligibility_for_registry(
        "1", research_state=state, registry=registry
    ).can_start
    blocked = research_start_eligibility_for_registry("2", research_state=state, registry=registry)
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_laboratory_level(3)
    assert RESEARCH_BY_ID["2"].tier == 2


def test_dependency_blocks_research_2_without_research_1() -> None:
    state = ResearchState()
    blocked = research_start_eligibility(
        "2",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=3,
    )
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_research(("1",))


def test_dependency_allows_research_2_after_research_1_completed() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    allowed = research_start_eligibility(
        "2",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=3,
    )
    assert allowed.can_start is True
    assert allowed.lock_reason is None


def test_carrier_speed_research_requires_technology_1() -> None:
    state = ResearchState()
    blocked = research_start_eligibility(
        "carrier_speed_1",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=1,
    )
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_research(("1",))

    state.start_research("1")
    state.mark_research_completed("1")
    allowed = research_start_eligibility(
        "carrier_speed_1",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=1,
    )
    assert allowed.can_start is True


def test_dependency_blocks_research_4_without_prior_tech_chain() -> None:
    state = ResearchState()
    blocked = research_start_eligibility(
        "4",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=9,
    )
    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_research(("3",))


def test_dependency_allows_research_4_when_chain_completed() -> None:
    state = ResearchState()
    for research_id in ("1", "2", "3"):
        state.start_research(research_id)
        state.mark_research_completed(research_id)
    allowed = research_start_eligibility(
        "4",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=9,
    )
    assert allowed.can_start is True


def test_research_1_has_no_dependency_gate() -> None:
    state = ResearchState()
    assert research_start_eligibility(
        "1",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=1,
    ).can_start


def test_statue_foundation_requires_excavation_research() -> None:
    state = ResearchState()
    for research_id in ("1", "2"):
        state.start_research(research_id)
        state.mark_research_completed(research_id)

    blocked = research_start_eligibility(
        "statue_foundation",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=3,
    )

    assert blocked.can_start is False
    assert blocked.lock_reason == lock_reason_requires_research(("statue_excavation",))

    state.start_research("statue_excavation")
    state.mark_research_completed("statue_excavation")
    allowed = research_start_eligibility(
        "statue_foundation",
        research_state=state,
        has_completed_laboratory=True,
        laboratory_level=3,
    )
    assert allowed.can_start is True


def test_lock_reasons_ru_locale(use_locale) -> None:
    with use_locale("ru"):
        assert lock_reason_no_laboratory() == i18n.t("ui.lock.no_laboratory")
        assert lock_reason_requires_research(("1",)) == i18n.t(
            "ui.lock.requires_research_one",
            name=i18n.t("research.1.name"),
        )
