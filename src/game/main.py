"""Application entry point for the game window and main loop."""

import pygame

from game.config import WINDOW_SIZE
from game.render import Renderer
from game.world import World


def main() -> int:
    """Run the main game loop until a quit event is received."""
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Isometric Strategy")

    world = World()
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            screen.fill((20, 24, 22))
            Renderer.draw_world(screen, world)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
