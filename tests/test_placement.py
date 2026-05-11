"""Placement controller: grid snap, spend + registry integration."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.cow_farm import CowFarm
from game.buildings.vineyard_farm import VineyardFarm
from game.buildings.forester_hut import ForesterHut
from game.buildings.lumber_camp import LumberCamp
from game.buildings.stone_mine import StoneMine
from game.config import TILE_H, TILE_W
from game.iso import screen_to_tile, world_to_screen
from game.render import Renderer
from game.ui.placement import PlacementController
from game.ui.placement import (
    _building_range_border_tiles,
    _pending_building_range_border_tiles,
    _placement_zone_specs,
    _placement_zones_follow_existing_buildings,
)
from game.world import World
from game.buildings.farm import Farm
from game.buildings.town_hall import TownHall
from game.config import CONSTRUCTION_REQUIREMENTS, town_hall_origin_tile
from game.workers import (
    FARMER_FIELD_RADIUS,
    FORESTER_PLANT_RADIUS,
    LUMBER_CAMP_RESOURCE_RADIUS,
    STONE_MINE_RESOURCE_RADIUS,
    building_center_tile,
    select_farmer_field_target,
)


def _cell_center_screen(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + TILE_W // 2, oy + sy + TILE_H // 2


def test_place_vineyard_farm_requires_town_hall_gate_and_starts_construction() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    placement = PlacementController(world, registry)
    placement.select("VINEYARD_FARM")
    cx, cy = _cell_center_screen(surface, world, 12, 12)
    assert placement.try_place(surface, (cx, cy))
    farms = [b for b in registry.all() if b.type_tag == "VINEYARD_FARM"]
    assert len(farms) == 1
    assert isinstance(farms[0], VineyardFarm)
    assert farms[0].is_under_construction
    site = farms[0].construction_site
    assert site is not None
    spec = CONSTRUCTION_REQUIREMENTS["VINEYARD_FARM"][1]
    assert site.required_resources == dict(spec.cost)
    assert site.build_time_ms == spec.build_time_ms


def test_place_cow_farm_requires_town_hall_gate_and_starts_construction() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    placement = PlacementController(world, registry)
    placement.select("COW_FARM")
    cx, cy = _cell_center_screen(surface, world, 12, 12)
    assert placement.try_place(surface, (cx, cy))
    cows = [b for b in registry.all() if b.type_tag == "COW_FARM"]
    assert len(cows) == 1
    assert isinstance(cows[0], CowFarm)
    assert cows[0].is_under_construction
    site = cows[0].construction_site
    assert site is not None
    spec = CONSTRUCTION_REQUIREMENTS["COW_FARM"][1]
    assert site.required_resources == dict(spec.cost)
    assert site.build_time_ms == spec.build_time_ms


def test_place_lumber_camp_is_free() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    cx, cy = _cell_center_screen(surface, world, 10, 10)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 1


def test_cancel_prevents_place() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    placement.cancel()
    cx, cy = _cell_center_screen(surface, world, 10, 10)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 0


def test_placement_does_not_require_wallet_resources() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("FARM")
    cx, cy = _cell_center_screen(surface, world, 12, 12)
    placement.try_place(surface, (cx, cy))
    assert len(registry.all()) == 1


def test_update_hover_uses_renderer_map_origin() -> None:
    """Hover cell must match visual tile picking with the same offset as `Renderer.draw_world`."""
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    ox, oy = Renderer.map_origin(surface, world)
    mx, my = 512, 360
    placement.update_hover(surface, (mx, my))
    exp = screen_to_tile(mx - ox, my - oy)
    assert placement.hover_grid == exp


def test_update_hover_keeps_cursor_inside_right_half_of_same_tile() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select("LUMBER_CAMP")
    gx, gy = 12, 12
    center_x, center_y = _cell_center_screen(surface, world, gx, gy)

    placement.update_hover(surface, (center_x + TILE_W // 2 - 1, center_y))

    assert placement.hover_grid == (gx, gy)


def test_building_range_border_tiles_uses_farmer_anchor_and_radius() -> None:
    farm = Farm(level=1, grid_pos=(10, 10))
    tiles = _building_range_border_tiles(farm, radius=FARMER_FIELD_RADIUS)
    fx, fy = building_center_tile(farm)
    assert (fx + FARMER_FIELD_RADIUS, fy) in tiles
    assert (fx - FARMER_FIELD_RADIUS, fy) in tiles
    assert (fx, fy + FARMER_FIELD_RADIUS) in tiles
    assert (fx, fy - FARMER_FIELD_RADIUS) in tiles


def test_field_placement_border_matches_farmer_target_radius() -> None:
    farm = Farm(level=1, grid_pos=(10, 10))
    farm_home = building_center_tile(farm)
    border = _building_range_border_tiles(farm, radius=FARMER_FIELD_RADIUS)
    field_phases = {tile: "EMPTY" for tile in border}

    assert select_farmer_field_target(
        farm_home=farm_home,
        field_phases=field_phases,
        max_radius=FARMER_FIELD_RADIUS,
    ) in border

    outside = {(farm_home[0] + FARMER_FIELD_RADIUS + 1, farm_home[1]): "EMPTY"}
    assert select_farmer_field_target(
        farm_home=farm_home,
        field_phases=outside,
        max_radius=FARMER_FIELD_RADIUS,
    ) is None


def test_field_zones_follow_existing_farms_but_gather_zones_follow_pending_building() -> None:
    from game.buildings.field import Field

    assert _placement_zones_follow_existing_buildings(Field)
    assert not _placement_zones_follow_existing_buildings(Farm)
    assert not _placement_zones_follow_existing_buildings(LumberCamp)
    assert not _placement_zones_follow_existing_buildings(StoneMine)
    assert not _placement_zones_follow_existing_buildings(ForesterHut)


def test_pending_gather_building_border_uses_future_building_center() -> None:
    grid_pos = (20, 30)
    tiles = _pending_building_range_border_tiles(
        LumberCamp,
        grid_pos,
        radius=LUMBER_CAMP_RESOURCE_RADIUS,
    )
    gx, gy = grid_pos
    w, h = LumberCamp.footprint
    center = (gx + w // 2, gy + h // 2)

    assert (center[0] + LUMBER_CAMP_RESOURCE_RADIUS, center[1]) in tiles
    assert (center[0] - LUMBER_CAMP_RESOURCE_RADIUS, center[1]) in tiles
    assert (center[0], center[1] + LUMBER_CAMP_RESOURCE_RADIUS) in tiles
    assert (center[0], center[1] - LUMBER_CAMP_RESOURCE_RADIUS) in tiles


def test_placement_zone_specs_for_gather_buildings_match_worker_radii() -> None:
    assert _placement_zone_specs(Farm) == [("FARM", FARMER_FIELD_RADIUS)]
    from game.buildings.field import Field

    assert _placement_zone_specs(Field) == [("FARM", FARMER_FIELD_RADIUS)]
    assert _placement_zone_specs(LumberCamp) == [("LUMBER_CAMP", LUMBER_CAMP_RESOURCE_RADIUS)]
    assert _placement_zone_specs(StoneMine) == [("STONE_MINE", STONE_MINE_RESOURCE_RADIUS)]
    assert _placement_zone_specs(ForesterHut) == [("FORESTER_HUT", FORESTER_PLANT_RADIUS)]
