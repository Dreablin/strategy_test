"""Placement mode: isometric snap preview, validity tint, and build actions."""

from __future__ import annotations

from typing import Type

import pygame

from game.buildings.base import Building
from game.buildings.costs import build_cost
from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.camera import Camera
from game.buildings.stone_mine import StoneMine
from game.config import TILE_H, TILE_W
from game.iso import screen_to_world, world_to_screen
from game.render import Renderer
from game.resources import ResourceManager
from game.world import World

_TAG_TO_CLASS: dict[str, Type[Building]] = {
    "LUMBER_CAMP": LumberCamp,
    "STONE_MINE": StoneMine,
    "IRON_MINE": IronMine,
    "FARM": Farm,
}


def _diamond_screen_points(
    origin_x: int, origin_y: int, gx: int, gy: int
) -> list[tuple[int, int]]:
    sx, sy = world_to_screen(gx, gy)
    px, py = origin_x + sx, origin_y + sy
    hw, hh = TILE_W // 2, TILE_H // 2
    return [
        (px + hw, py),
        (px + TILE_W - 1, py + hh),
        (px + hw, py + TILE_H - 1),
        (px, py + hh),
    ]


class PlacementController:
    """Tracks pending building type, hover cell, preview tint, and commits via registry."""

    __slots__ = ("_camera", "_hover", "_pending", "_registry", "_resources", "_world")

    def __init__(
        self,
        world: World,
        registry: BuildingRegistry,
        resources: ResourceManager,
        camera: Camera | None = None,
    ) -> None:
        self._world = world
        self._registry = registry
        self._resources = resources
        self._camera = camera if camera is not None else Camera()
        self._pending: Type[Building] | None = None
        self._hover: tuple[int, int] | None = None

    @property
    def pending_type(self) -> Type[Building] | None:
        return self._pending

    @property
    def hover_grid(self) -> tuple[int, int] | None:
        """Current snapped grid cell under the cursor while a type is selected (tests / debug)."""
        return self._hover

    def cancel(self) -> None:
        self._pending = None
        self._hover = None

    def select(self, building_type: str) -> None:
        cls = _TAG_TO_CLASS.get(building_type)
        if cls is None:
            return
        self._pending = cls
        self._hover = None

    def update_hover(
        self,
        surface: pygame.Surface,
        screen_pos: tuple[int, int],
        camera: Camera | None = None,
    ) -> None:
        if self._pending is None:
            self._hover = None
            return
        ox, oy = Renderer.map_origin(surface, self._world)
        mx, my = screen_pos
        cam = camera if camera is not None else self._camera
        gx, gy = screen_to_world(mx - cam.offset[0] - ox, my - cam.offset[1] - oy)
        self._hover = (gx, gy)

    def try_place(
        self,
        surface: pygame.Surface,
        screen_pos: tuple[int, int],
        camera: Camera | None = None,
    ) -> bool:
        if self._pending is None:
            return False
        self.update_hover(surface, screen_pos, camera)
        if self._hover is None:
            return False
        gx, gy = self._hover
        cls = self._pending
        if not self._registry.can_place(cls, (gx, gy)):
            return False
        cost = build_cost(cls.type_tag)
        if not self._resources.try_spend(cost):
            return False
        self._registry.place(cls, (gx, gy))
        return True

    def draw(self, surface: pygame.Surface, camera=None) -> None:
        if self._pending is None or self._hover is None:
            return
        gx, gy = self._hover
        cls = self._pending
        w, h = cls.footprint
        ox, oy = Renderer.map_origin(surface, self._world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        ox += cam_x
        oy += cam_y
        valid = self._registry.can_place(cls, (gx, gy)) and self._resources.has(
            build_cost(cls.type_tag)
        )
        color = (40, 220, 80, 100) if valid else (220, 50, 50, 100)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                pts = _diamond_screen_points(ox, oy, tx, ty)
                pygame.draw.polygon(overlay, color, pts)
        surface.blit(overlay, (0, 0))
