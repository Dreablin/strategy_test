"""Gates and stubs for research point accumulation (PRD F-RES / phase 28)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.research_state import ResearchState


def sync_research_delivered_from_laboratory(
    *,
    research_state: ResearchState,
    laboratory: Laboratory,
) -> None:
    """Align domain delivered bookkeeping with Laboratory local input storage."""
    if not research_state.has_active_research():
        return
    for resource in laboratory.research_input_resources():
        target = laboratory.research_input_amount(resource)
        current = research_state.delivered_amounts().get(resource, 0)
        delta = target - current
        if delta > 0:
            research_state.add_delivered(resource, delta)


def research_points_may_accumulate(
    *,
    research_state: ResearchState,
    laboratory: Laboratory,
) -> bool:
    """True when active research exists and every required input is stored locally."""
    if not research_state.has_active_research():
        return False
    if not laboratory.has_research_input_storage():
        return False
    return laboratory.all_research_inputs_delivered()


def research_points_for_elapsed_ms(
    *,
    laboratory: Laboratory,
    active_scientist_count: int,
    elapsed_ms: int,
) -> int:
    """Points earned over *elapsed_ms*, linear in active Scientists up to slot capacity."""
    if active_scientist_count <= 0 or elapsed_ms <= 0:
        return 0
    capacity = laboratory.scientist_slot_capacity()
    contributing = min(active_scientist_count, capacity)
    rate = laboratory.research_points_per_scientist_per_second()
    return (rate * contributing * int(elapsed_ms)) // 1000


def tick_laboratory_research_points(
    *,
    research_state: ResearchState,
    laboratory: Laboratory,
    active_scientist_count: int,
    now_ms: int,
    last_tick_by_laboratory: dict[int, int],
) -> None:
    """Advance research points for one Laboratory timestep."""
    if not research_state.has_active_research():
        return
    lab_id = id(laboratory)
    last_ms = last_tick_by_laboratory.get(lab_id)
    last_tick_by_laboratory[lab_id] = int(now_ms)
    if last_ms is None:
        return
    elapsed_ms = int(now_ms) - int(last_ms)
    if elapsed_ms <= 0:
        return
    points = research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=active_scientist_count,
        elapsed_ms=elapsed_ms,
    )
    if points <= 0:
        return
    try_accumulate_research_points(
        research_state=research_state,
        laboratory=laboratory,
        points=points,
    )


def try_accumulate_research_points(
    *,
    research_state: ResearchState,
    laboratory: Laboratory,
    points: int,
) -> int:
    """Add *points* only after all research inputs are delivered; return amount added."""
    if points <= 0:
        return 0
    if not research_points_may_accumulate(
        research_state=research_state,
        laboratory=laboratory,
    ):
        return 0
    sync_research_delivered_from_laboratory(
        research_state=research_state,
        laboratory=laboratory,
    )
    research_state.add_points(points)
    return points
