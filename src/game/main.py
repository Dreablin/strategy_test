"""Application entry point for the game window and main loop."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.config import WINDOW_SIZE
from game.input import GameInput
from game.loop import apply_production_tick
from game.render import Renderer
from game.resources import ResourceManager
from game.tick import TickScheduler
from game.ui.bottom_bar import BottomBar
from game.ui.placement import PlacementController
from game.ui.top_bar import TopBar
from game.world import World
from game.workers import WorkerManager


def main() -> int:
    """Run the main game loop until a quit event is received."""
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Isometric Strategy")

    world = World()
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    # Player starts with a single Town Hall as required by core game rules.
    registry.place(TownHall, (16, 16))
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    worker_manager = WorkerManager(resources, registry)
    game_input = GameInput(world, registry, resources, placement, worker_manager, camera)
    scheduler = TickScheduler()

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    game_input.handle(screen, event)
            if game_input.consume_camera_moved():
                # Clamp in the same coordinate space used by rendering:
                # world pixel bounds + renderer origin for the current surface.
                origin_x, origin_y = Renderer.map_origin(screen, world)
                min_x, min_y, max_x, max_y = Renderer.world_pixel_bounds(world)
                camera.clamp(
                    WINDOW_SIZE,
                    (min_x + origin_x, min_y + origin_y, max_x + origin_x, max_y + origin_y),
                )

            if scheduler.update(pygame.time.get_ticks()):
                apply_production_tick(registry, resources, worker_manager)
                registry.sync_resources_per_cycle(
                    resources, staffed_buildings=worker_manager.working_buildings()
                )

            screen.fill((20, 24, 22))
            Renderer.draw_world(screen, world, camera)
            Renderer.draw_buildings(screen, world, registry, camera)
            Renderer.draw_workers(screen, world, registry, worker_manager, camera)
            TopBar.draw(screen, resources)
            BottomBar.draw(screen, resources)
            placement.draw(screen, camera)
            game_input.draw_panel(screen)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
