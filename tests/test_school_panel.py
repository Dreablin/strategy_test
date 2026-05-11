"""School panel: hire rows and click actions."""

import pygame

from game.buildings.school import SCHOOL_QUEUE_CAPACITY, SCHOOL_TRAINING_MS
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.buildings.registry import BuildingRegistry
from game.config import town_hall_origin_tile
from game.input import GameInput
from game.ui.placement import PlacementController
from game.ui.school_panel import SchoolPanel
from game.workers import WorkerManager
from game.world import World


def test_school_panel_hire_click_returns_worker_action() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    worker_type, rect = layout.hire_buttons[0]
    assert (
        SchoolPanel.click_action(surface, rect.center, school, worker_assigned=False)
        == f"hire:{worker_type}"
    )


def test_school_panel_demolish_click_returns_demolish() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    assert SchoolPanel.click_action(surface, layout.demolish.center, school, worker_assigned=False) == "demolish"


def test_school_panel_upgrade_click_returns_upgrade() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    assert layout.upgrade is not None
    assert SchoolPanel.click_action(surface, layout.upgrade.center, school, worker_assigned=False) == "upgrade"


def test_school_panel_upgrade_disabled_while_training_queue_not_empty() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")

    layout = SchoolPanel.layout(surface, school, worker_assigned=False)

    assert layout.upgrade is not None
    assert layout.upgrade_enabled is False
    assert SchoolPanel.click_action(surface, layout.upgrade.center, school, worker_assigned=False) is None


def test_school_panel_upgrade_reenabled_after_training_completes_or_is_cancelled() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    assert school.update_training(SCHOOL_TRAINING_MS) == "LUMBERJACK"

    completed_layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    assert completed_layout.upgrade_enabled is True

    assert school.enqueue_training("FARMER")
    assert school.cancel_training_at(0)
    cancelled_layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    assert cancelled_layout.upgrade_enabled is True


def test_school_panel_layout_contains_configured_training_slots() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    assert len(layout.queue_slots) == SCHOOL_QUEUE_CAPACITY
    assert any(worker_type == "CARRIER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "BUILDER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "SAWYER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "MILLER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "BAKER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "ANIMAL_HERDER" for worker_type, _ in layout.hire_buttons)
    assert any(worker_type == "WATERMAN" for worker_type, _ in layout.hire_buttons)
    assert layout.hire_buttons[0][0] == "CARRIER"
    assert layout.hire_buttons[1][0] == "BUILDER"
    assert len(layout.hire_buttons) == 13


def test_school_panel_draws_yellow_progress_for_active_training_slot() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    school.update_training(SCHOOL_TRAINING_MS // 2)
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)

    SchoolPanel.draw(surface, school, worker_assigned=False)

    slot = layout.queue_slots[0]
    found_yellow = False
    for x in range(slot.left, slot.right):
        pixel = surface.get_at((x, slot.bottom - 3))
        if pixel.r > 180 and pixel.g > 180 and pixel.b < 120:
            found_yellow = True
            break
    assert found_yellow


def test_school_panel_clicking_queue_slot_returns_cancel_action() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    assert school.enqueue_training("LUMBERJACK")
    assert school.enqueue_training("FARMER")
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)

    assert SchoolPanel.click_action(surface, layout.queue_slots[0].center, school, worker_assigned=False) == "cancel:0"
    assert SchoolPanel.click_action(surface, layout.queue_slots[1].center, school, worker_assigned=False) == "cancel:1"
    assert SchoolPanel.click_action(surface, layout.queue_slots[2].center, school, worker_assigned=False) is None


def test_school_panel_basic_tier_shows_all_basic_workers() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    worker_types = [wt for wt, _ in layout.hire_buttons]
    assert "CARRIER" in worker_types
    assert "BUILDER" in worker_types
    assert "LUMBERJACK" in worker_types
    assert "FARMER" in worker_types
    assert "ANIMAL_HERDER" in worker_types
    assert len(worker_types) == 13


def test_school_panel_advanced_tier_shows_winemaker() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="advanced")
    worker_types = [wt for wt, _ in layout.hire_buttons]
    assert "WINEMAKER" in worker_types


def test_school_panel_default_tier_is_basic() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout_default = SchoolPanel.layout(surface, school, worker_assigned=False)
    layout_basic = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    default_types = [wt for wt, _ in layout_default.hire_buttons]
    basic_types = [wt for wt, _ in layout_basic.hire_buttons]
    assert default_types == basic_types


def test_school_panel_layout_has_two_tabs() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    assert len(layout.tabs) == 2
    tab_tiers = [t for t, _ in layout.tabs]
    assert tab_tiers == ["basic", "advanced"]
    assert layout.active_tier == "basic"


def test_school_panel_click_tab_returns_tab_action() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    adv_rect = layout.tabs[1][1]
    action = SchoolPanel.click_action(surface, adv_rect.center, school, worker_assigned=False, tier="basic")
    assert action == "tab:advanced"


def test_school_panel_active_tier_advanced_layout() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="advanced")
    assert layout.active_tier == "advanced"
    worker_types = [wt for wt, _ in layout.hire_buttons]
    assert "WINEMAKER" in worker_types


def test_school_panel_frame_size_stays_fixed_between_hire_tiers() -> None:
    surface = pygame.Surface((900, 700))
    school = School(level=1, grid_pos=(10, 10))

    basic = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    advanced = SchoolPanel.layout(surface, school, worker_assigned=False, tier="advanced")

    assert basic.frame.size == advanced.frame.size
    assert basic.frame.topleft == advanced.frame.topleft
    assert len(basic.hire_buttons) > len(advanced.hire_buttons)


def test_game_input_school_tier_switches_on_tab_click() -> None:
    from game.camera import Camera

    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, (15, 15))
    school.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    camera = Camera()
    placement = PlacementController(world, registry)
    gi = GameInput(world, registry, placement, workers, camera)
    gi._panel = school  # noqa: SLF001
    assert gi._school_tier == "basic"  # noqa: SLF001

    surface = pygame.Surface((900, 700))
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, tier="basic")
    adv_pos = layout.tabs[1][1].center
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=adv_pos)
    gi.handle(surface, click_event)
    assert gi._school_tier == "advanced"  # noqa: SLF001

    layout2 = SchoolPanel.layout(surface, school, worker_assigned=False, tier="advanced")
    basic_pos = layout2.tabs[0][1].center
    click_event2 = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=basic_pos)
    gi.handle(surface, click_event2)
    assert gi._school_tier == "basic"  # noqa: SLF001
