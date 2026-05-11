"""Placement mode: isometric snap preview, validity tint, and build actions."""

from __future__ import annotations

import random
from typing import Type

import pygame

from game.buildings.base import Building
from game.buildings.canteen import Canteen
from game.buildings.chicken_farm import ChickenFarm
from game.buildings.cow_farm import CowFarm
from game.buildings.bakery import Bakery
from game.buildings.field import Field
from game.buildings.farm import Farm
from game.buildings.forester_hut import ForesterHut
from game.buildings.house import House
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.mill import Mill
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.sawmill import Sawmill
from game.buildings.vineyard import Vineyard
from game.buildings.vineyard_farm import VineyardFarm
from game.buildings.well import Well
from game.buildings.winery import Winery
from game.camera import Camera
from game.buildings.stone_mine import StoneMine
from game.config import TILE_H, TILE_W, building_int_setting
from game.iso import screen_to_tile, world_to_screen
from game.iron import IronDeposit
from game.render import Renderer
from game.stones import Stone
from game.world import World
from game.workers import (
    FARMER_FIELD_RADIUS,
    FORESTER_PLANT_RADIUS,
    LUMBER_CAMP_RESOURCE_RADIUS,
    STONE_MINE_RESOURCE_RADIUS,
    building_center_tile,
)

_TAG_TO_CLASS: dict[str, Type[Building]] = {
    "LUMBER_CAMP": LumberCamp,
    "STONE_MINE": StoneMine,
    "IRON_MINE": IronMine,
    "FARM": Farm,
    "FIELD": Field,
    "FORESTER_HUT": ForesterHut,
    "SCHOOL": School,
    "HOUSE": House,
    "CANTEEN": Canteen,
    "SAWMILL": Sawmill,
    "MILL": Mill,
    "BAKERY": Bakery,
    "CHICKEN_FARM": ChickenFarm,
    "COW_FARM": CowFarm,
    "VINEYARD_FARM": VineyardFarm,
    "VINEYARD": Vineyard,
    "WELL": Well,
    "WINERY": Winery,
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


def _building_search_anchor_tile(building: Building) -> tuple[int, int] | None:
    if building.grid_pos is None:
        return None
    return building_center_tile(building)


def _building_range_border_tiles(building: Building, radius: int) -> set[tuple[int, int]]:
    center = _building_search_anchor_tile(building)
    if center is None:
        return set()
    return _range_border_tiles(center, radius)


def _pending_building_range_border_tiles(
    cls: Type[Building],
    grid_pos: tuple[int, int],
    radius: int,
) -> set[tuple[int, int]]:
    gx, gy = grid_pos
    w, h = cls.footprint
    return _range_border_tiles((gx + w // 2, gy + h // 2), radius)


def _range_border_tiles(center: tuple[int, int], radius: int) -> set[tuple[int, int]]:
    cx, cy = center
    border: set[tuple[int, int]] = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if max(abs(dx), abs(dy)) != radius:
                continue
            border.add((cx + dx, cy + dy))
    return border


def _placement_zones_follow_existing_buildings(cls: Type[Building] | None) -> bool:
    return cls is Field


def _placement_zone_specs(cls: Type[Building] | None) -> list[tuple[str, int]]:
    if cls is Farm:
        return [("FARM", FARMER_FIELD_RADIUS)]
    if cls is VineyardFarm:
        return [
            (
                "VINEYARD_FARM",
                building_int_setting("VINEYARD_FARM", "harvest", "radius_cells"),
            )
        ]
    if cls is Field:
        return [("FARM", FARMER_FIELD_RADIUS)]
    if cls is LumberCamp:
        return [("LUMBER_CAMP", LUMBER_CAMP_RESOURCE_RADIUS)]
    if cls is StoneMine:
        return [("STONE_MINE", STONE_MINE_RESOURCE_RADIUS)]
    if cls is ForesterHut:
        return [("FORESTER_HUT", FORESTER_PLANT_RADIUS)]
    return []


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
        self._pending_dev: str | None = None  # DEV_TREE | DEV_STONE | DEV_IRON
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
        if tool_type not in {"DEV_TREE", "DEV_STONE", "DEV_IRON"}:
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
        gx, gy = screen_to_tile(mx - cam.offset[0] - ox, my - cam.offset[1] - oy)
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
            if (
                self._world.is_occupied(gx, gy)
                or self._world.is_tree_blocking(gx, gy)
                or self._world.is_stone_blocking(gx, gy)
                or self._world.iron_deposit_at(gx, gy) is not None
                or self._world.gold_deposit_at(gx, gy) is not None
            ):
                return False
            return self._world.plant_tree(gx, gy, now_ms=0) is not None
        if self._pending_dev == "DEV_STONE":
            if not self._world.is_in_grass(gx, gy):
                return False
            if (
                self._world.is_occupied(gx, gy)
                or self._world.is_tree_blocking(gx, gy)
                or self._world.is_stone_blocking(gx, gy)
                or self._world.iron_deposit_at(gx, gy) is not None
                or self._world.gold_deposit_at(gx, gy) is not None
            ):
                return False
            self._world._stones[(gx, gy)] = Stone(variant=random.randint(0, 4))  # noqa: SLF001
            return True
        if self._pending_dev == "DEV_IRON":
            if not self._world.is_in_grass(gx, gy):
                return False
            if (
                self._world.is_occupied(gx, gy)
                or self._world.is_tree_blocking(gx, gy)
                or self._world.is_stone_blocking(gx, gy)
                or self._world.iron_deposit_at(gx, gy) is not None
                or self._world.gold_deposit_at(gx, gy) is not None
            ):
                return False
            self._world._iron[(gx, gy)] = IronDeposit(blocking=False, variant=random.randint(0, 4))  # noqa: SLF001
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
                and self._world.iron_deposit_at(gx, gy) is None
                and self._world.gold_deposit_at(gx, gy) is None
            )
        ox, oy = Renderer.map_origin(surface, self._world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        ox += cam_x
        oy += cam_y
        color = (40, 220, 80, 100) if valid else (220, 50, 50, 100)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        zone_specs = _placement_zone_specs(cls)
        if zone_specs:
            zone_color = (120, 190, 255, 110)
            if _placement_zones_follow_existing_buildings(cls):
                type_to_radius = {tag: radius for tag, radius in zone_specs}
                for building in self._registry.all():
                    radius = type_to_radius.get(building.type_tag)
                    if radius is None or building.grid_pos is None:
                        continue
                    for tx, ty in _building_range_border_tiles(building, radius=radius):
                        if not self._world.is_in_grass(tx, ty):
                            continue
                        pts = _diamond_screen_points(ox, oy, tx, ty)
                        pygame.draw.polygon(overlay, zone_color, pts, width=1)
            elif cls is not None:
                for _tag, radius in zone_specs:
                    for tx, ty in _pending_building_range_border_tiles(cls, (gx, gy), radius=radius):
                        if not self._world.is_in_grass(tx, ty):
                            continue
                        pts = _diamond_screen_points(ox, oy, tx, ty)
                        pygame.draw.polygon(overlay, zone_color, pts, width=1)
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                pts = _diamond_screen_points(ox, oy, tx, ty)
                pygame.draw.polygon(overlay, color, pts)
        surface.blit(overlay, (0, 0))
