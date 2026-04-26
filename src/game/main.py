"""Application entry point for the game window and main loop."""

import pygame

from game.buildings.registry import BuildingRegistry
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

            if scheduler.update(pygame.time.get_ticks()):
                apply_production_tick(registry, resources, worker_manager)
                registry.sync_resources_per_cycle(
                    resources, staffed_buildings=worker_manager.staffed_buildings()
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
