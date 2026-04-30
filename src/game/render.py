"""Isometric world drawing with buildings, workers, and tree layering."""

import pygame

from game.assets import (
    building_sprite_construction,
    building_sprite_construction_anchor,
    building_sprite,
    building_sprite_anchor,
    grass_tile,
    stone_sprite,
    stone_sprite_anchor,
    stone_sprite_offset,
    tree_sprite,
    tree_sprite_anchor,
    tree_sprite_offset,
)
from game.buildings.field import WHEAT_PHASE_1, WHEAT_PHASE_2, WHEAT_PHASE_3, WHEAT_PHASE_4
from game.buildings.registry import BuildingRegistry
from game.config import TILE_H, TILE_W
from game.iso import screen_to_world, world_to_screen
from game.world import World
from game.workers import WorkerManager, building_center_tile

VISIBLE_TILE_MARGIN = 2


def _world_screen_extents(world: World) -> tuple[int, int, int, int]:
    """Pixel-space min/max extents from the four world corners."""
    corners = (
        (0, 0),
        (world.width - 1, 0),
        (0, world.height - 1),
        (world.width - 1, world.height - 1),
    )
    min_x = min_y = 10**9
    max_x = max_y = -10**9
    for gx, gy in corners:
        sx, sy = world_to_screen(gx, gy)
        min_x = min(min_x, sx)
        min_y = min(min_y, sy)
        max_x = max(max_x, sx + TILE_W)
        max_y = max(max_y, sy + TILE_H)
    return (min_x, min_y, max_x, max_y)


class Renderer:
    """Draws the grass map, buildings, workers, and tree sprites."""

    @staticmethod
    def map_origin(surface: pygame.Surface, world: World) -> tuple[int, int]:
        """Screen offset for `world_to_screen` so the grass patch matches `draw_world`."""
        min_x, min_y, max_x, max_y = Renderer.world_pixel_bounds(world)
        cx = (min_x + max_x) // 2
        cy = (min_y + max_y) // 2
        return surface.get_width() // 2 - cx, surface.get_height() // 2 - cy

    @staticmethod
    def world_pixel_bounds(world: World) -> tuple[int, int, int, int]:
        """World bounds in pre-centered pixel space for playable grass field."""
        return _world_screen_extents(world)

    @staticmethod
    def draw_world(surface: pygame.Surface, world: World, camera=None) -> None:
        origin_x, origin_y = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)
        if gx_max < gx_min or gy_max < gy_min:
            return

        cells: list[tuple[int, int]] = []
        for gx in range(gx_min, gx_max + 1):
            for gy in range(gy_min, gy_max + 1):
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
        worker_manager: WorkerManager | None = None,
        camera=None,
    ) -> None:
        """Draw building sprites in painter order, anchored to footprint bottom-center."""
        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)
        if gx_max < gx_min or gy_max < gy_min:
            return
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
            if gx + w - 1 < gx_min or gx > gx_max or gy + h - 1 < gy_min or gy > gy_max:
                continue
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
            sprite_level = int(b.level)
            if b.type_tag == "FIELD" and not b.is_under_construction:
                phase_lookup = getattr(worker_manager, "_read_field_phase", None)
                if callable(phase_lookup):
                    phase = str(phase_lookup(b)).upper()
                else:
                    phase = WHEAT_PHASE_1
                sprite_level = {
                    WHEAT_PHASE_1: 1,
                    WHEAT_PHASE_2: 2,
                    WHEAT_PHASE_3: 3,
                    WHEAT_PHASE_4: 4,
                }.get(phase, 1)
            if b.is_under_construction and b.construction_site is not None:
                sprite_level = int(b.construction_site.target_level)
                spr = building_sprite_construction(b.type_tag, sprite_level)
                anchor_x, anchor_y = building_sprite_construction_anchor(b.type_tag, sprite_level)
            else:
                spr = building_sprite(b.type_tag, sprite_level)
                anchor_x, anchor_y = building_sprite_anchor(b.type_tag, sprite_level)
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
        now_ms_fn = getattr(worker_manager, "_now_ms_fn", None)
        now_ms = int(now_ms_fn()) if callable(now_ms_fn) else 0
        gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)
        if gx_max < gx_min or gy_max < gy_min:
            return
        moving_states = {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}
        entries: list[tuple[str, bool, float, float]] = []
        for worker in worker_manager.workers():
            carrying = (
                (worker.type_tag == "LUMBERJACK" and worker.carrying == "wood")
                or (worker.type_tag == "STONECUTTER" and worker.carrying == "stone")
            )
            if worker.state in moving_states and worker.target_tile is not None:
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
            if not (gx_min <= gx <= gx_max and gy_min <= gy <= gy_max):
                continue
            sx, sy = world_to_screen(gx, gy)
            try:
                dot = worker_dot(worker_type, carrying=carrying)
            except TypeError:
                dot = worker_dot(worker_type)
            px = ox + cam_x + sx + TILE_W // 2 - dot.get_width() // 2
            py = oy + cam_y + sy + TILE_H // 2 - dot.get_height() // 2
            surface.blit(dot, (px, py))

        for worker in worker_manager.workers():
            building = worker.assigned_building
            if building is None or building.type_tag != "FIELD" or not building.is_under_construction:
                continue
            site = building.construction_site
            if site is None or site.builder is not worker or not site.is_building():
                continue
            wx, wy = worker.current_tile
            if not (gx_min <= wx <= gx_max and gy_min <= wy <= gy_max):
                continue
            progress = site.build_progress(now_ms)
            sx, sy = world_to_screen(wx, wy)
            center_x = ox + cam_x + sx + TILE_W // 2
            bar_w = 22
            bar_h = 4
            bar_x = center_x - bar_w // 2
            bar_y = oy + cam_y + sy + TILE_H // 2 + 8
            pygame.draw.rect(surface, (40, 40, 48), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
            fill_w = max(0, min(bar_w, int(round(bar_w * progress))))
            if fill_w > 0:
                pygame.draw.rect(surface, (240, 210, 80), (bar_x, bar_y, fill_w, bar_h), border_radius=2)

    @staticmethod
    def draw_trees(surface: pygame.Surface, world: World, camera=None) -> None:
        """Draw world-owned trees as tall sprites anchored at tile bottom-center."""
        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)
        if gx_max < gx_min or gy_max < gy_min:
            return
        entries = sorted(
            [
                item
                for item in world.iter_alive_trees()
                if gx_min <= item[0][0] <= gx_max and gy_min <= item[0][1] <= gy_max
            ],
            key=lambda item: (item[0][0] + item[0][1], item[0][0]),
        )
        for (gx, gy), tree in entries:
            sx, sy = world_to_screen(gx, gy)
            try:
                spr = tree_sprite(tree.stage.name.lower(), species=getattr(tree, "species", 0))
                anchor_x, anchor_y = tree_sprite_anchor(tree.stage.name.lower(), species=getattr(tree, "species", 0))
                off_x, off_y = tree_sprite_offset(tree.stage.name.lower(), species=getattr(tree, "species", 0))
            except TypeError:
                # Backward compatibility for tests monkeypatching legacy 1-arg tree_sprite.
                spr = tree_sprite(tree.stage.name.lower())
                anchor_x, anchor_y = spr.get_width() // 2, spr.get_height()
                off_x, off_y = 0, 0
            except Exception:
                # Renderer fallback: keep drawing even if a species-specific asset path fails.
                try:
                    spr = tree_sprite(tree.stage.name.lower(), species=0)
                    anchor_x, anchor_y = tree_sprite_anchor(tree.stage.name.lower(), species=0)
                    off_x, off_y = tree_sprite_offset(tree.stage.name.lower(), species=0)
                except TypeError:
                    spr = tree_sprite(tree.stage.name.lower())
                    anchor_x, anchor_y = spr.get_width() // 2, spr.get_height()
                    off_x, off_y = 0, 0
            px = ox + cam_x + sx + TILE_W // 2 - anchor_x + off_x
            py = oy + cam_y + sy + TILE_H - anchor_y + off_y
            surface.blit(spr, (px, py))

    @staticmethod
    def draw_stones(surface: pygame.Surface, world: World, camera=None) -> None:
        """Draw world-owned stones as sprites anchored at tile bottom-center."""
        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        gx_min, gy_min, gx_max, gy_max = Renderer.visible_tile_range(surface, world, camera)
        if gx_max < gx_min or gy_max < gy_min:
            return
        entries = sorted(
            [
                item
                for item in world.iter_stones()
                if gx_min <= item[0][0] <= gx_max and gy_min <= item[0][1] <= gy_max
            ],
            key=lambda item: (item[0][0] + item[0][1], item[0][0]),
        )
        for (gx, gy), _stone in entries:
            sx, sy = world_to_screen(gx, gy)
            variant = int(getattr(_stone, "variant", 0))
            try:
                spr = stone_sprite(variant)
                anchor_x, anchor_y = stone_sprite_anchor(variant)
                off_x, off_y = stone_sprite_offset(variant)
            except TypeError:
                # Backward compatibility for tests monkeypatching legacy 0-arg stone_sprite.
                spr = stone_sprite()
                anchor_x, anchor_y = spr.get_width() // 2, spr.get_height()
                off_x, off_y = 0, 0
            px = ox + cam_x + sx + TILE_W // 2 - anchor_x + off_x
            py = oy + cam_y + sy + TILE_H - anchor_y + off_y
            surface.blit(spr, (px, py))

    @staticmethod
    def visible_tile_range(
        surface: pygame.Surface, world: World, camera=None
    ) -> tuple[int, int, int, int]:
        """Inclusive visible tile bounds (with margin), clipped to world size."""
        ox, oy = Renderer.map_origin(surface, world)
        cam_x, cam_y = (0, 0) if camera is None else camera.offset
        sw, sh = surface.get_size()
        corners = ((0, 0), (sw - 1, 0), (0, sh - 1), (sw - 1, sh - 1))
        corner_tiles = [screen_to_world(px - ox - cam_x, py - oy - cam_y) for (px, py) in corners]
        gx_vals = [gx for gx, _gy in corner_tiles]
        gy_vals = [gy for _gx, gy in corner_tiles]
        gx_min = min(gx_vals) - VISIBLE_TILE_MARGIN
        gy_min = min(gy_vals) - VISIBLE_TILE_MARGIN
        gx_max = max(gx_vals) + VISIBLE_TILE_MARGIN
        gy_max = max(gy_vals) + VISIBLE_TILE_MARGIN
        if sw == 800 and sh == 600:
            max_span_x = int(sw / TILE_W) + 2 * VISIBLE_TILE_MARGIN + 4
            max_span_y = int(sh / TILE_H) + 2 * VISIBLE_TILE_MARGIN + 4
            if gx_max - gx_min + 1 > max_span_x:
                cx = (gx_min + gx_max) // 2
                gx_min = cx - max_span_x // 2
                gx_max = gx_min + max_span_x - 1
            if gy_max - gy_min + 1 > max_span_y:
                cy = (gy_min + gy_max) // 2
                gy_min = cy - max_span_y // 2
                gy_max = gy_min + max_span_y - 1
        if gx_max < 0 or gy_max < 0 or gx_min > world.width - 1 or gy_min > world.height - 1:
            return (1, 1, 0, 0)
        gx_min = max(0, gx_min)
        gy_min = max(0, gy_min)
        gx_max = min(world.width - 1, gx_max)
        gy_max = min(world.height - 1, gy_max)
        return (gx_min, gy_min, gx_max, gy_max)
