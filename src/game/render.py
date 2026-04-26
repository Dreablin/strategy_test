"""Isometric world drawing (grass field and decorative tree skirt)."""

import pygame

from game.assets import building_sprite, grass_tile, tree_tile
from game.buildings.registry import BuildingRegistry
from game.config import TILE_H, TILE_W
from game.iso import world_to_screen
from game.world import World
from game.workers import WorkerManager, building_center_tile

_TREE_RING_TILES = 2


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
    """Draws the static grass map plus an outer ring of non-playable tree tiles."""

    @staticmethod
    def map_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
        """Screen offset for `world_to_screen` so the grass patch matches `draw_world`."""
        return _compute_grass_origin(surface, world)

    @staticmethod
    def draw_world(surface: pygame.Surface, world: World, camera=None) -> None:
        origin_x, origin_y = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        lo = -_TREE_RING_TILES
        hi_w = world.width + _TREE_RING_TILES
        hi_h = world.height + _TREE_RING_TILES

        cells: list[tuple[int, int, bool]] = []
        for gx in range(lo, hi_w):
            for gy in range(lo, hi_h):
                cells.append((gx, gy, world.is_in_grass(gx, gy)))
        cells.sort(key=lambda c: (c[0] + c[1], c[0]))

        g_tile = grass_tile()
        t_tile = tree_tile()
        for gx, gy, in_grass in cells:
            sx, sy = world_to_screen(gx, gy)
            tile = g_tile if in_grass else t_tile
            surface.blit(tile, (origin_x + cam_x + sx, origin_y + cam_y + sy))

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
            dx = ox + cam_x + foot_cx - spr.get_width() // 2
            dy = oy + cam_y + foot_by - spr.get_height()
            surface.blit(spr, (dx, dy))

    @staticmethod
    def worker_grid_positions(
        registry: BuildingRegistry, worker_manager: WorkerManager
    ) -> list[tuple[str, tuple[int, int]]]:
        """Grid positions for worker dots: assigned center, idle stack near Town Hall, orphan tile."""
        town_hall = next((b for b in registry.all() if b.type_tag == "TOWN_HALL"), None)
        th_center = building_center_tile(town_hall) if town_hall is not None else (0, 0)
        out: list[tuple[str, tuple[int, int]]] = []
        idle_i = 0
        for worker in worker_manager.workers():
            if worker.assigned_building is not None:
                out.append((worker.type_tag, building_center_tile(worker.assigned_building)))
                continue
            if town_hall is not None and worker.stand_tile in ((0, 0), th_center):
                out.append((worker.type_tag, (th_center[0] + 1 + idle_i, th_center[1])))
                idle_i += 1
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
        """Draw worker dots at grid positions returned by `worker_grid_positions`."""
        from game.assets import worker_dot

        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        positions = Renderer.worker_grid_positions(registry, worker_manager)
        positions.sort(key=lambda item: sum(item[1]))
        for worker_type, (gx, gy) in positions:
            sx, sy = world_to_screen(gx, gy)
            dot = worker_dot(worker_type)
            px = ox + cam_x + sx + TILE_W // 2 - dot.get_width() // 2
            py = oy + cam_y + sy + TILE_H // 2 - dot.get_height() // 2
            surface.blit(dot, (px, py))
