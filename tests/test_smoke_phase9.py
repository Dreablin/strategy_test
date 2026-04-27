"""Phase 9 end-to-end smoke test in dummy SDL mode."""

from __future__ import annotations

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.config import WINDOW_SIZE
from game.input import GameInput
from game.iso import world_to_screen
from game.loop import apply_production_tick
from game.render import Renderer
from game.resources import ResourceManager
from game.tick import TickScheduler
from game.ui.bottom_bar import BUILD_MENU_SELECT
from game.ui.placement import PlacementController
from game.world import World
from game.workers import WorkerManager


def _tile_click_pos(
    surface: pygame.Surface,
    world: World,
    camera: Camera,
    gx: int,
    gy: int,
) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return (ox + sx + camera.offset[0] + 16, oy + sy + camera.offset[1] + 16)


def _is_approach_tile(building, tile: tuple[int, int]) -> bool:
    bx, by = building.grid_pos  # type: ignore[misc]
    bw, bh = type(building).footprint
    x, y = tile
    cheb = max(
        max(bx - x, x - (bx + bw - 1), 0),
        max(by - y, y - (by + bh - 1), 0),
    )
    return cheb == 1


def test_smoke_phase9_worker_moves_and_production_gates() -> None:
    screen = pygame.Surface(WINDOW_SIZE)
    world = World()
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    workers = WorkerManager(resources, registry)
    game_input = GameInput(world, registry, resources, placement, workers, camera)
    scheduler = TickScheduler()
    registry.place(TownHall, (16, 16))

    # 1) Build Lumber Camp at a valid location through input routing.
    game_input.handle(screen, pygame.event.Event(BUILD_MENU_SELECT, building_type="LUMBER_CAMP"))
    camp_click = _tile_click_pos(screen, world, camera, 22, 22)
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=camp_click)
    )
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame.BUTTON_LEFT, pos=camp_click)
    )
    camp = next((b for b in registry.all() if b.type_tag == "LUMBER_CAMP"), None)
    assert camp is not None

    # 2) Hire a Lumberjack directly and trigger assignment recalculation.
    assert workers.hire("LUMBERJACK") is not None
    workers.reassign_all()
    worker = workers.workers()[0]
    assert worker.assigned_building is camp
    assert worker.state == "moving"

    # 3) Advance simulated time: worker must move and eventually reach approach tile.
    start_tile = worker.current_tile
    workers.update(3000)
    mid_tile = worker.current_tile
    workers.update(120000)
    end_tile = worker.current_tile
    assert mid_tile != start_tile
    assert worker.state == "working"
    assert _is_approach_tile(camp, end_tile)

    # 4) Production gating: Lumber Camp has no passive production in Phase 11.
    world2 = World()
    resources2 = ResourceManager()
    registry2 = BuildingRegistry(world2)
    registry2.place(TownHall, (16, 16))
    registry2.place(LumberCamp, (24, 24))
    workers2 = WorkerManager(resources2, registry2)
    assert workers2.hire("LUMBERJACK") is not None
    workers2.reassign_all()
    wood_before = resources2.get("wood")
    assert scheduler.update(10_000) is True
    apply_production_tick(registry2, resources2, workers2)
    assert resources2.get("wood") == wood_before
    workers2.update(120_000)
    wood_before = resources2.get("wood")
    assert scheduler.update(20_000) is True
    apply_production_tick(registry2, resources2, workers2)
    assert resources2.get("wood") == wood_before

    # 5) Spacing rule: touching is rejected, one-tile gap is accepted.
    assert not registry.can_place(LumberCamp, (24, 22))
    assert registry.can_place(LumberCamp, (25, 22))
