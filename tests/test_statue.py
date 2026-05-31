"""Mission Statue building, staging, UI, and construction delivery controls."""

from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from game.assets import building_sprite, building_sprite_anchor, building_sprite_construction
from game.buildings.registry import BuildingRegistry
from game.buildings.statue import Statue
from game.buildings.town_hall import TownHall
from game.config import CONSTRUCTION_REQUIREMENTS, near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.mission import statue_completed
from game.research_state import ResearchState
from game.transport_tasks import construction_transport_tasks
from game.ui.bottom_bar import BUILD_MENU_SELECT, BottomBar, _button_rects
from game.ui.building_panel import _upgrade_cost_lines, _upgrade_label
from game.ui.construction_panel import ConstructionPanel
from game.ui.placement import PlacementController, _TAG_TO_CLASS
from game.ui.statue_panel import StatuePanel
from game.worker_models import TransportTask, Worker
from game.workers import WorkerManager
from game.world import World


def _registry() -> tuple[World, BuildingRegistry, TownHall]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    return world, registry, town_hall


def _complete_research(state: ResearchState, research_id: str) -> None:
    state.start_research(research_id)
    state.mark_research_completed(research_id)


def test_statue_registered_for_placement_and_construction() -> None:
    assert _TAG_TO_CLASS["STATUE"] is Statue
    assert "STATUE" in CONSTRUCTION_REQUIREMENTS
    assert set(CONSTRUCTION_REQUIREMENTS["STATUE"]) == {1, 2, 3, 4}

    world, registry, _town_hall = _registry()
    placement = PlacementController(world, registry)
    placement.select("STATUE")

    assert placement.has_pending
    assert placement.pending_type is Statue


def test_statue_placement_requires_excavation_research_when_bound() -> None:
    _world, registry, _town_hall = _registry()
    state = ResearchState()
    registry.bind_research_state(state)

    assert not registry.can_place(Statue, near_town_hall_tile(10, 10))

    _complete_research(state, "statue_excavation")
    assert registry.can_place(Statue, near_town_hall_tile(10, 10))


def test_statue_upgrade_requires_next_stage_research_when_bound() -> None:
    _world, registry, _town_hall = _registry()
    state = ResearchState()
    registry.bind_research_state(state)
    _complete_research(state, "statue_excavation")
    statue = registry.place(Statue, near_town_hall_tile(10, 10))
    statue.construction_site = None

    assert registry.upgrade_building(statue) is False
    assert statue.construction_site is None

    _complete_research(state, "statue_foundation")
    assert registry.upgrade_building(statue) is True
    assert statue.construction_site is not None
    assert statue.construction_site.target_level == 2


def test_statue_has_four_named_stages() -> None:
    statue = Statue(level=1, grid_pos=(4, 4))
    assert statue.max_level() == 4
    assert statue.stage_name(1) == "Excavation"
    assert statue.stage_name(2) == "Foundation"
    assert statue.stage_name(3) == "Pedestal"
    assert statue.stage_name(4) == "Statue"
    assert statue.next_stage_name() == "Foundation"
    assert _upgrade_label(statue) == "Start stage: Foundation"


def test_statue_unique_and_not_demolishable() -> None:
    _world, registry, _town_hall = _registry()
    first = registry.place(Statue, near_town_hall_tile(10, 10))
    assert not registry.can_place(Statue, near_town_hall_tile(24, 24))
    with pytest.raises(ValueError, match="invalid placement"):
        registry.place(Statue, near_town_hall_tile(24, 24))

    registry.demolish(first)

    assert first in registry.all()
    assert not registry.can_place(Statue, near_town_hall_tile(24, 24))


def test_statue_assets_resolve_with_meta() -> None:
    root = Path(__file__).resolve().parents[1] / "assets" / "buildings" / "statue"
    assert (root / "asset_meta.json").is_file()
    for level in (1, 4):
        sprite = building_sprite("STATUE", level)
        assert sprite.get_width() > 0 and sprite.get_height() > 0
        ax, ay = building_sprite_anchor("STATUE", level)
        assert 0 <= ax <= sprite.get_width()
        assert 0 <= ay <= sprite.get_height()
        construction = building_sprite_construction("STATUE", level)
        assert construction.get_width() > 0 and construction.get_height() > 0


def test_social_menu_click_statue_emits_event() -> None:
    surface = pygame.Surface((1400, 720))
    BottomBar._menu = "social"  # noqa: SLF001
    entries = ("back", "school", "house", "canteen", "restaurant", "laboratory", "statue")
    statue_rect = _button_rects(surface, len(entries))[entries.index("statue")]

    pygame.event.clear()
    BottomBar.handle_click(surface, statue_rect.center)

    events = [event for event in pygame.event.get() if event.type == BUILD_MENU_SELECT]
    assert len(events) == 1
    assert events[0].building_type == "STATUE"


def test_statue_panel_hides_demolish_and_uses_stage_upgrade() -> None:
    surface = pygame.Surface((1280, 720))
    statue = Statue(level=1, grid_pos=(4, 4))
    statue.construction_site = None
    layout = StatuePanel.layout(surface, statue)

    assert layout.demolish is None
    assert layout.upgrade is not None
    assert StatuePanel.click_action(surface, layout.upgrade.center, statue) == "upgrade"
    assert StatuePanel.click_action(surface, layout.frame.bottomleft, statue) is None
    StatuePanel.draw(surface, statue)
    assert surface.get_at(layout.frame.center)[:3] != (0, 0, 0)


def test_statue_panel_disables_unresearched_next_stage() -> None:
    surface = pygame.Surface((1280, 720))
    state = ResearchState()
    statue = Statue(level=1, grid_pos=(4, 4))
    statue.construction_site = None

    layout = StatuePanel.layout(surface, statue, research_state=state)

    assert layout.upgrade is not None
    assert layout.upgrade_enabled is False
    assert StatuePanel.click_action(
        surface,
        layout.upgrade.center,
        statue,
        research_state=state,
    ) is None

    _complete_research(state, "statue_foundation")
    unlocked = StatuePanel.layout(surface, statue, research_state=state)
    assert unlocked.upgrade_enabled is True


def test_statue_upgrade_tooltip_shows_next_stage_research() -> None:
    statue = Statue(level=1, grid_pos=(4, 4))
    assert "Requires research: Foundation Engineering" in _upgrade_cost_lines(statue)

    statue.level = 2
    assert "Requires research: Pedestal Masonry" in _upgrade_cost_lines(statue)

    statue.level = 3
    assert "Requires research: Monument Assembly" in _upgrade_cost_lines(statue)


def test_construction_panel_statue_stage_toggle_and_no_demolish() -> None:
    surface = pygame.Surface((1280, 720))
    statue = Statue(level=1, grid_pos=(4, 4))
    statue.construction_site = ConstructionSite(
        required_resources={"stone": 2},
        delivered_resources={},
        build_time_ms=1000,
        build_started_ms=None,
        builder=None,
        target_level=2,
    )
    layout = ConstructionPanel.layout(surface, statue)

    assert ConstructionPanel.title_line(statue) == "Building: Foundation"
    assert layout.demolish is None
    assert layout.toggle is not None
    assert ConstructionPanel.click_action(surface, layout.toggle.center, statue) == "toggle_construction_deliveries"


def test_paused_statue_construction_skips_transport_planning() -> None:
    _world, registry, town_hall = _registry()
    statue = registry.place(Statue, near_town_hall_tile(10, 10))
    town_hall.add_to_warehouse("stone", 100)

    assert any(task.target is statue for task in construction_transport_tasks(registry))

    statue.set_construction_deliveries_enabled(False)

    assert not any(task.target is statue for task in construction_transport_tasks(registry))


def test_worker_manager_removes_queued_paused_statue_construction_tasks() -> None:
    _world, registry, town_hall = _registry()
    statue = registry.place(Statue, near_town_hall_tile(10, 10))
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.enqueue_transport_task(
        resource="stone",
        source=town_hall,
        target=statue,
        priority=10,
        purpose="construction",
    )

    statue.set_construction_deliveries_enabled(False)
    workers.update(0)

    assert not [task for task in workers._transport_queue if task.target is statue]  # noqa: SLF001


def test_paused_statue_construction_cancels_assigned_task_before_pickup() -> None:
    _world, registry, town_hall = _registry()
    statue = registry.place(Statue, near_town_hall_tile(10, 10))
    worker = Worker("CARRIER", stand_tile=town_hall.grid_pos)
    worker.transport_task = TransportTask("stone", town_hall, statue, priority=10, purpose="construction")
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers._workers.append(worker)  # noqa: SLF001

    statue.set_construction_deliveries_enabled(False)
    workers.update(0)

    assert worker.transport_task is None
    assert worker.carrying is None
    assert worker.idle is True


def test_paused_statue_construction_allows_carried_resource_to_finish() -> None:
    _world, registry, town_hall = _registry()
    statue = registry.place(Statue, near_town_hall_tile(10, 10))
    worker = Worker("CARRIER", stand_tile=town_hall.grid_pos)
    task = TransportTask("stone", town_hall, statue, priority=10, purpose="construction")
    worker.transport_task = task
    worker.carrying = "stone"
    worker.state = "moving"
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers._workers.append(worker)  # noqa: SLF001

    statue.set_construction_deliveries_enabled(False)
    workers.update(0)

    assert worker.transport_task is task
    assert worker.carrying == "stone"


def test_statue_completed_marks_mission_goal() -> None:
    _world, registry, _town_hall = _registry()
    statue = registry.place(Statue, near_town_hall_tile(10, 10))
    statue.construction_site = None
    statue.level = 3
    assert statue_completed(registry) is False

    statue.level = 4

    assert statue.mission_complete is True
    assert statue_completed(registry) is True
