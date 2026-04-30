"""Placement mode: isometric snap preview, validity tint, and build actions."""

from __future__ import annotations

from typing import Type

import pygame

from game.buildings.base import Building
from game.buildings.farm import Farm
from game.buildings.forester_hut import ForesterHut
from game.buildings.house import House
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.camera import Camera
from game.buildings.stone_mine import StoneMine
from game.config import TILE_H, TILE_W
from game.iso import screen_to_world, world_to_screen
from game.render import Renderer
from game.stones import Stone
from game.world import World

_TAG_TO_CLASS: dict[str, Type[Building]] = {
    "LUMBER_CAMP": LumberCamp,
    "STONE_MINE": StoneMine,
    "IRON_MINE": IronMine,
    "FARM": Farm,
    "FORESTER_HUT": ForesterHut,
    "SCHOOL": School,
    "HOUSE": House,
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

    __slots__ = ("_camera", "_hover", "_pending", "_pending_dev", "_registry", "_world")

    def __init__(
        self,
        world: World,
        registry: BuildingRegistry,
        camera: Camera | None = None,
    ) -> None:
        self._world = world
        self._registry = registry
        self._camera = camera if camera is not None else Camera()
        self._pending: Type[Building] | None = None
        self._pending_dev: str | None = None  # DEV_TREE | DEV_STONE
        self._hover: tuple[int, int] | None = None

    @property
    def pending_type(self) -> Type[Building] | None:
        return self._pending

    @property
    def has_pending(self) -> bool:
        """Whether any placement tool (building or dev) is currently selected."""
        return self._pending is not None or self._pending_dev is not None

    @property
    def hover_grid(self) -> tuple[int, int] | None:
        """Current snapped grid cell under the cursor while a type is selected (tests / debug)."""
        return self._hover

    def cancel(self) -> None:
        self._pending = None
        self._pending_dev = None
        self._hover = None

    def select(self, building_type: str) -> None:
        cls = _TAG_TO_CLASS.get(building_type)
        if cls is None:
            return
        self._pending = cls
        self._pending_dev = None
        self._hover = None

    def select_dev(self, tool_type: str) -> None:
        if tool_type not in {"DEV_TREE", "DEV_STONE"}:
            return
        self._pending = None
        self._pending_dev = tool_type
        self._hover = None

    def update_hover(
        self,
        surface: pygame.Surface,
        screen_pos: tuple[int, int],
        camera: Camera | None = None,
    ) -> None:
        if self._pending is None:
            if self._pending_dev is None:
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
            if self._pending_dev is None:
                return False
        self.update_hover(surface, screen_pos, camera)
        if self._hover is None:
            return False
        gx, gy = self._hover
        cls = self._pending
        if cls is not None:
            if not self._registry.can_place(cls, (gx, gy)):
                return False
            self._registry.place(cls, (gx, gy))
            return True
        if self._pending_dev == "DEV_TREE":
            if not self._world.is_in_grass(gx, gy):
                return False
            if self._world.is_occupied(gx, gy) or self._world.is_tree_blocking(gx, gy) or self._world.is_stone_blocking(gx, gy):
                return False
            return self._world.plant_tree(gx, gy, now_ms=0) is not None
        if self._pending_dev == "DEV_STONE":
            if not self._world.is_in_grass(gx, gy):
                return False
            if self._world.is_occupied(gx, gy) or self._world.is_tree_blocking(gx, gy) or self._world.is_stone_blocking(gx, gy):
                return False
            self._world._stones[(gx, gy)] = Stone()  # noqa: SLF001
            return True
        return False

    def draw(self, surface: pygame.Surface, camera=None) -> None:
        if (self._pending is None and self._pending_dev is None) or self._hover is None:
            return
        gx, gy = self._hover
        cls = self._pending
        if cls is not None:
            w, h = cls.footprint
            valid = self._registry.can_place(cls, (gx, gy))
        else:
            w, h = 1, 1
            valid = (
                self._world.is_in_grass(gx, gy)
                and not self._world.is_occupied(gx, gy)
                and not self._world.is_tree_blocking(gx, gy)
                and not self._world.is_stone_blocking(gx, gy)
            )
        ox, oy = Renderer.map_origin(surface, self._world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        ox += cam_x
        oy += cam_y
        color = (40, 220, 80, 100) if valid else (220, 50, 50, 100)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                pts = _diamond_screen_points(ox, oy, tx, ty)
                pygame.draw.polygon(overlay, color, pts)
        surface.blit(overlay, (0, 0))
