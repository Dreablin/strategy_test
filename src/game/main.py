"""Application entry point for the game window and main loop."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.config import WINDOW_SIZE
from game.render import Renderer
from game.resources import ResourceManager
from game.ui.bottom_bar import BAR_HEIGHT, BUILD_MENU_SELECT, BottomBar
from game.ui.placement import PlacementController
from game.ui.top_bar import TopBar
from game.world import World

# Must match `TopBar` strip height so clicks/hover ignore the HUD area.
_TOP_BAR_HEIGHT = 48


def main() -> int:
    """Run the main game loop until a quit event is received."""
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Isometric Strategy")

    world = World()
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry, resources)

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == BUILD_MENU_SELECT:
                    placement.select(event.building_type)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    placement.cancel()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == pygame.BUTTON_LEFT:
                        _h = screen.get_height()
                        if event.pos[1] >= _h - BAR_HEIGHT:
                            BottomBar.handle_click(screen, event.pos, resources)
                        elif event.pos[1] >= _TOP_BAR_HEIGHT:
                            placement.try_place(screen, event.pos)
                    elif event.button == pygame.BUTTON_RIGHT:
                        placement.cancel()
                elif event.type == pygame.MOUSEMOTION:
                    _h = screen.get_height()
                    if _TOP_BAR_HEIGHT <= event.pos[1] < _h - BAR_HEIGHT:
                        placement.update_hover(screen, event.pos)

            screen.fill((20, 24, 22))
            Renderer.draw_world(screen, world)
            TopBar.draw(screen, resources)
            BottomBar.draw(screen, resources)
            placement.draw(screen)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
