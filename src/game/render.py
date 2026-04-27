"""Isometric world drawing with buildings, workers, and tree layering."""

import pygame

from game.assets import (
    building_sprite,
    building_sprite_anchor,
    grass_tile,
    tree_sprite,
)
from game.buildings.registry import BuildingRegistry
from game.config import TILE_H, TILE_W
from game.iso import world_to_screen
from game.world import World
from game.workers import WorkerManager, building_center_tile


def _compute_grass_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
    """Shift so the playable grass patch is roughly centered on the surface."""
    min_x = min_y = 10**9
    max_x = max_y = -10**9
    for gx in range(world.width):
        for gy in range(world.height):
            sx, sy = world_to_screen(gx, gy)
            min_x = min(min_x, sx)
            min_y = min(min_y, sy)
            max_x = max(max_x, sx + TILE_W)
            max_y = max(max_y, sy + TILE_H)
    cx = (min_x + max_x) // 2
    cy = (min_y + max_y) // 2
    return surface.get_width() // 2 - cx, surface.get_height() // 2 - cy


class Renderer:
    """Draws the grass map, buildings, workers, and tree sprites."""

    @staticmethod
    def map_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
        """Screen offset for `world_to_screen` so the grass patch matches `draw_world`."""
        return _compute_grass_origin(surface, world)

    @staticmethod
    def world_pixel_bounds(world: World) -> tuple[int, int, int, int]:
        """World bounds in pre-centered pixel space for playable grass field."""
        min_x = min_y = 10**9
        max_x = max_y = -10**9
        for gx in range(world.width):
            for gy in range(world.height):
                sx, sy = world_to_screen(gx, gy)
                min_x = min(min_x, sx)
                min_y = min(min_y, sy)
                max_x = max(max_x, sx + TILE_W)
                max_y = max(max_y, sy + TILE_H)
        return (min_x, min_y, max_x, max_y)

    @staticmethod
    def draw_world(surface: pygame.Surface, world: World, camera=None) -> None:
        origin_x, origin_y = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset

        cells: list[tuple[int, int]] = []
        for gx in range(world.width):
            for gy in range(world.height):
                cells.append((gx, gy))
        cells.sort(key=lambda c: (c[0] + c[1], c[0]))

        g_tile = grass_tile()
        for gx, gy in cells:
            sx, sy = world_to_screen(gx, gy)
            px, py = origin_x + cam_x + sx, origin_y + cam_y + sy
            surface.blit(g_tile, (px, py))

    @staticmethod
    def draw_buildings(
        surface: pygame.Surface,
        world: World,
        registry: BuildingRegistry,
        camera=None,
    ) -> None:
        """Draw building sprites in painter order, anchored to footprint bottom-center."""
        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        draw_surface = surface.inner if hasattr(surface, "inner") else surface
        buildings = sorted(
            registry.all(),
            key=lambda b: (b.grid_pos[0] + b.grid_pos[1], b.grid_pos[0]) if b.grid_pos else (10**9, 10**9),
        )
        for b in buildings:
            pos = b.grid_pos
            if pos is None:
                continue
            gx, gy = pos
            w, h = type(b).footprint
            base_color = (96, 84, 72) if b.type_tag == "TOWN_HALL" else (88, 78, 66)
            min_x = 10**9
            min_y = 10**9
            max_x = -10**9
            max_y = -10**9
            for tx in range(gx, gx + w):
                for ty in range(gy, gy + h):
                    sx, sy = world_to_screen(tx, ty)
                    px = ox + cam_x + sx
                    py = oy + cam_y + sy
                    hw, hh = TILE_W // 2, TILE_H // 2
                    pts = [
                        (px + hw, py),
                        (px + TILE_W - 1, py + hh),
                        (px + hw, py + TILE_H - 1),
                        (px, py + hh),
                    ]
                    pygame.draw.polygon(draw_surface, base_color, pts)
                    min_x = min(min_x, sx)
                    min_y = min(min_y, sy)
                    max_x = max(max_x, sx + TILE_W)
                    max_y = max(max_y, sy + TILE_H)
            foot_cx = (min_x + max_x) // 2
            foot_by = max_y
            spr = building_sprite(b.type_tag, b.level)
            anchor_x, anchor_y = building_sprite_anchor(b.type_tag, b.level)
            dx = ox + cam_x + foot_cx - anchor_x
            dy = oy + cam_y + foot_by - anchor_y
            surface.blit(spr, (dx, dy))

    @staticmethod
    def worker_grid_positions(
        registry: BuildingRegistry, worker_manager: WorkerManager
    ) -> list[tuple[str, tuple[int, int]]]:
        """Grid positions for worker dots: assigned center, idle stack near Town Hall, orphan tile."""
        out: list[tuple[str, tuple[int, int]]] = []
        for worker in worker_manager.workers():
            if worker.assigned_building is not None:
                out.append((worker.type_tag, building_center_tile(worker.assigned_building)))
                continue
            out.append((worker.type_tag, worker.stand_tile))
        return out

    @staticmethod
    def draw_workers(
        surface: pygame.Surface,
        world: World,
        registry: BuildingRegistry,
        worker_manager: WorkerManager,
        camera=None,
    ) -> None:
        """Draw worker dots; moving workers are interpolated between tile centers."""
        from game.assets import worker_dot

        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        entries: list[tuple[str, bool, float, float]] = []
        for worker in worker_manager.workers():
            carrying = worker.carrying == "wood"
            if worker.state == "moving" and worker.target_tile is not None:
                cx, cy = worker.current_tile
                tx, ty = worker.target_tile
                t = max(0.0, min(1.0, worker.segment_progress))
                entries.append((worker.type_tag, carrying, cx + (tx - cx) * t, cy + (ty - cy) * t))
                continue
            if worker.assigned_building is not None:
                if worker.state == "working":
                    wx, wy = building_center_tile(worker.assigned_building)
                else:
                    wx, wy = worker.current_tile
                entries.append((worker.type_tag, carrying, float(wx), float(wy)))
                continue
            sxg, syg = worker.stand_tile
            entries.append((worker.type_tag, carrying, float(sxg), float(syg)))

        entries.sort(key=lambda item: item[2] + item[3])
        for worker_type, carrying, gx, gy in entries:
            sx, sy = world_to_screen(gx, gy)
            try:
                dot = worker_dot(worker_type, carrying=carrying)
            except TypeError:
                dot = worker_dot(worker_type)
            px = ox + cam_x + sx + TILE_W // 2 - dot.get_width() // 2
            py = oy + cam_y + sy + TILE_H // 2 - dot.get_height() // 2
            surface.blit(dot, (px, py))

    @staticmethod
    def draw_trees(surface: pygame.Surface, world: World, camera=None) -> None:
        """Draw world-owned trees as tall sprites anchored at tile bottom-center."""
        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        entries = sorted(world.iter_alive_trees(), key=lambda item: (item[0][0] + item[0][1], item[0][0]))
        for (gx, gy), tree in entries:
            sx, sy = world_to_screen(gx, gy)
            spr = tree_sprite(tree.stage.name.lower())
            px = ox + cam_x + sx + TILE_W // 2 - spr.get_width() // 2
            py = oy + cam_y + sy + TILE_H - spr.get_height()
            surface.blit(spr, (px, py))
