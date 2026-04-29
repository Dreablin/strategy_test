"""Application entry point for the game window and main loop."""

import pygame

from game import dev_asset_reload
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall, bootstrap_starting_warehouse
from game.camera import Camera
from game.config import TOWN_HALL_STARTING_WAREHOUSE, WINDOW_SIZE, town_hall_origin_tile
from game.input import TOP_BAR_HEIGHT, GameInput
from game.render import Renderer
from game.housing import current_population, max_population
from game.ui.bottom_bar import BAR_HEIGHT, BottomBar
from game.ui.placement import PlacementController
from game.ui.top_bar import TopBar
from game.world import World
from game.workers import WorkerManager


def main() -> int:
    """Run the main game loop until a quit event is received."""
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("Isometric Strategy")

    world = World()
    registry = BuildingRegistry(world)
    # Player starts with a single Town Hall as required by core game rules.
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    bootstrap_starting_warehouse(town_hall, TOWN_HALL_STARTING_WAREHOUSE)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    worker_manager = WorkerManager(registry, now_ms_fn=pygame.time.get_ticks)
    worker_manager.bootstrap_starting_workers_near_town_hall(town_hall)
    game_input = GameInput(world, registry, placement, worker_manager, camera)

    running = True
    try:
        while running:
            now_ms = pygame.time.get_ticks()
            camera_moved = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif dev_asset_reload.process_event(event):
                    continue
                elif event.type == pygame.VIDEORESIZE:
                    # Keep HUD fixed-height while letting world area grow/shrink.
                    min_w = 640
                    min_h = TOP_BAR_HEIGHT + BAR_HEIGHT + 120
                    new_w = max(min_w, int(event.w))
                    new_h = max(min_h, int(event.h))
                    screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                    camera_moved = True
                else:
                    game_input.handle(screen, event)
            camera_moved = camera_moved or game_input.consume_camera_moved()
            if camera_moved:
                # Clamp in the same coordinate space used by rendering:
                # world pixel bounds + renderer origin for the current surface.
                origin_x, origin_y = Renderer.map_origin(screen, world)
                min_x, min_y, max_x, max_y = Renderer.world_pixel_bounds(world)
                camera.clamp(
                    screen.get_size(),
                    (min_x + origin_x, min_y + origin_y, max_x + origin_x, max_y + origin_y),
                )

            worker_manager.update(now_ms)

            screen.fill((20, 24, 22))
            Renderer.draw_world(screen, world, camera)
            Renderer.draw_buildings(screen, world, registry, camera)
            Renderer.draw_stones(screen, world, camera)
            Renderer.draw_workers(screen, world, registry, worker_manager, camera)
            Renderer.draw_trees(screen, world, camera)
            TopBar.draw(
                screen,
                current_population=current_population(registry, worker_manager),
                max_population=max_population(registry, worker_manager),
            )
            BottomBar.draw(screen)
            placement.draw(screen, camera)
            game_input.draw_panel(screen)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
