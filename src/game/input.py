"""Mouse/keyboard routing: placement mode, building panel open/close (PRD F-INPUT / F-UI-PANEL)."""

from __future__ import annotations

import pygame

from game.buildings.base import Building
from game.buildings.registry import BuildingRegistry
from game.iso import screen_to_world
from game.render import Renderer
from game.resources import ResourceManager
from game.ui.bottom_bar import BAR_HEIGHT, BUILD_MENU_SELECT, BottomBar
from game.ui.building_panel import BuildingPanel
from game.ui.placement import PlacementController
from game.world import World

# Matches `TopBar` strip; clicks above this are HUD, not map.
TOP_BAR_HEIGHT = 48


def screen_to_grid(surface: pygame.Surface, world: World, screen_pos: tuple[int, int]) -> tuple[int, int]:
    """Map screen pixel to isometric grid cell using the same origin as ``Renderer.draw_world``."""
    ox, oy = Renderer.map_origin(surface, world)
    mx, my = screen_pos
    return screen_to_world(mx - ox, my - oy)


def _on_map(surface: pygame.Surface, pos: tuple[int, int]) -> bool:
    x, y = pos
    h = surface.get_height()
    return TOP_BAR_HEIGHT <= y < h - BAR_HEIGHT


class GameInput:
    """Owns building panel selection; delegates placement and bottom bar where appropriate."""

    __slots__ = ("_panel", "_placement", "_registry", "_resources", "_world")

    def __init__(
        self,
        world: World,
        registry: BuildingRegistry,
        resources: ResourceManager,
        placement: PlacementController,
    ) -> None:
        self._world = world
        self._registry = registry
        self._resources = resources
        self._placement = placement
        self._panel: Building | None = None

    @property
    def panel_building(self) -> Building | None:
        """Building shown in the modal, or ``None`` if the panel is closed."""
        return self._panel

    def _sync_panel_stale(self) -> None:
        if self._panel is not None and self._panel not in self._registry.all():
            self._panel = None

    def handle(self, surface: pygame.Surface, event: pygame.event.Event) -> None:
        self._sync_panel_stale()
        if event.type == BUILD_MENU_SELECT:
            self._panel = None
            self._placement.select(event.building_type)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._panel is not None:
                self._panel = None
            else:
                self._placement.cancel()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
            self._placement.cancel()
            self._panel = None
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            if not _on_map(surface, event.pos):
                if event.pos[1] >= surface.get_height() - BAR_HEIGHT:
                    BottomBar.handle_click(surface, event.pos, self._resources)
                return
            self._handle_map_left_click(surface, event.pos)
            return

    def update_placement_hover(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        if _on_map(surface, pos):
            self._placement.update_hover(surface, pos)

    def draw_panel(self, surface: pygame.Surface) -> None:
        self._sync_panel_stale()
        if self._panel is None:
            return
        BuildingPanel.draw(
            surface,
            self._panel,
            self._resources,
            worker_assigned=False,
        )

    def _handle_map_left_click(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        if self._placement.pending_type is not None:
            self._placement.try_place(surface, pos)
            return

        gx, gy = screen_to_grid(surface, self._world, pos)

        if self._panel is not None:
            layout = BuildingPanel.layout(
                surface,
                self._panel,
                self._resources,
                worker_assigned=False,
            )
            if layout.frame.collidepoint(pos):
                action = BuildingPanel.click_action(
                    surface,
                    pos,
                    self._panel,
                    self._resources,
                    worker_assigned=False,
                )
                if action == "close":
                    self._panel = None
                return

            self._panel = None
            target = self._registry.at(gx, gy)
            if target is not None:
                self._panel = target
            return

        hit = self._registry.at(gx, gy)
        if hit is not None:
            self._panel = hit
