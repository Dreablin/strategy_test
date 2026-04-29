"""Phase 8 smoke integration in dummy SDL mode."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.config import WINDOW_SIZE, near_town_hall_tile, town_hall_origin_tile
from game.input import GameInput
from game.iso import world_to_screen
from game.render import Renderer
from game.ui.bottom_bar import BUILD_MENU_SELECT, BottomBar
from game.ui.placement import PlacementController
from game.ui.top_bar import TopBar
from game.world import World
from game.workers import WorkerManager

_SENTINEL = (20, 24, 22)


def _render_frame(
    screen: pygame.Surface,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    placement: PlacementController,
    game_input: GameInput,
    camera: Camera,
) -> None:
    screen.fill(_SENTINEL)
    Renderer.draw_world(screen, world, camera)
    Renderer.draw_buildings(screen, world, registry, camera)
    Renderer.draw_workers(screen, world, registry, worker_manager, camera)
    TopBar.draw(screen, current_population=0, max_population=0)
    BottomBar.draw(screen)
    placement.draw(screen, camera)
    game_input.draw_panel(screen)


def test_smoke_phase8_build_draw_and_rmb_pan() -> None:
    screen = pygame.Surface(WINDOW_SIZE)
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    worker_manager = WorkerManager(registry)
    game_input = GameInput(world, registry, placement, worker_manager, camera)
    town_hall = registry.place(TownHall, town_hall_origin_tile())

    # 1) Initial render shows Town Hall.
    _render_frame(screen, world, registry, worker_manager, placement, game_input, camera)
    thx, thy = town_hall.grid_pos  # type: ignore[assignment]
    ox, oy = Renderer.map_origin(screen, world)
    sx, sy = world_to_screen(thx + 1, thy + 1)
    th_px = (ox + sx + 32, oy + sy + 16)
    assert screen.get_at(th_px)[:3] != _SENTINEL

    # 2) Place a Lumber Camp through input events and verify render.
    game_input.handle(screen, pygame.event.Event(BUILD_MENU_SELECT, building_type="LUMBER_CAMP"))
    psx, psy = world_to_screen(*near_town_hall_tile())
    place_pos = (ox + psx + camera.offset[0] + 16, oy + psy + camera.offset[1] + 16)
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=place_pos)
    )
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame.BUTTON_LEFT, pos=place_pos)
    )
    _render_frame(screen, world, registry, worker_manager, placement, game_input, camera)
    camp = next((b for b in registry.all() if b.type_tag == "LUMBER_CAMP"), None)
    assert camp is not None
    cgx, cgy = camp.grid_pos  # type: ignore[assignment]
    csx, csy = world_to_screen(cgx + 1, cgy + 1)
    camp_px = (ox + csx + camera.offset[0] + 32, oy + csy + camera.offset[1] + 16)
    assert screen.get_at(camp_px)[:3] != _SENTINEL

    # 3) RMB drag pan and assert offset movement + render remains safe.
    start = (400, 300)
    game_input.handle(screen, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_RIGHT, pos=start))
    game_input.handle(
        screen,
        pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(420, 300),
            rel=(20, 0),
            buttons=(0, 0, 1),
        ),
    )
    game_input.handle(
        screen,
        pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(440, 300),
            rel=(20, 0),
            buttons=(0, 0, 1),
        ),
    )
    game_input.handle(
        screen,
        pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(460, 300),
            rel=(20, 0),
            buttons=(0, 0, 1),
        ),
    )
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame.BUTTON_RIGHT, pos=(460, 300))
    )
    assert camera.offset[0] >= 60
    _render_frame(screen, world, registry, worker_manager, placement, game_input, camera)
