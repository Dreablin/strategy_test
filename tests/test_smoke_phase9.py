"""Phase 9 end-to-end smoke test in dummy SDL mode."""

from __future__ import annotations

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.config import WINDOW_SIZE, near_town_hall_tile, town_hall_origin_tile
from game.input import GameInput
from game.iso import world_to_screen
from game.render import Renderer
from game.trees import Tree, TreeStage
from game.ui.bottom_bar import BUILD_MENU_SELECT
from game.ui.placement import PlacementController
from game.world import World
from game.workers import WorkerManager


def _tile_click_pos(
    surface: pygame.Surface,
    world: World,
    camera: Camera,
    gx: int,
    gy: int,
) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return (ox + sx + camera.offset[0] + 16, oy + sy + camera.offset[1] + 16)


def _is_approach_tile(building, tile: tuple[int, int]) -> bool:
    bx, by = building.grid_pos  # type: ignore[misc]
    bw, bh = type(building).footprint
    x, y = tile
    cheb = max(
        max(bx - x, x - (bx + bw - 1), 0),
        max(by - y, y - (by + bh - 1), 0),
    )
    return cheb == 1


def test_smoke_phase9_worker_moves_and_production_gates() -> None:
    screen = pygame.Surface(WINDOW_SIZE)
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    game_input = GameInput(world, registry, placement, workers, camera)
    registry.place(TownHall, town_hall_origin_tile())

    # 1) Build Lumber Camp at a valid location through input routing.
    game_input.handle(screen, pygame.event.Event(BUILD_MENU_SELECT, building_type="LUMBER_CAMP"))
    cx, cy = near_town_hall_tile()
    camp_click = _tile_click_pos(screen, world, camera, cx, cy)
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=camp_click)
    )
    game_input.handle(
        screen, pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame.BUTTON_LEFT, pos=camp_click)
    )
    camp = next((b for b in registry.all() if b.type_tag == "LUMBER_CAMP"), None)
    assert camp is not None
    camp.construction_site = None
    cgx, cgy = camp.grid_pos  # type: ignore[assignment]
    world._trees[(cgx + 3, cgy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(cgx + 4, cgy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    # 2) Hire a Lumberjack directly and trigger assignment recalculation.
    assert workers.hire("LUMBERJACK") is not None
    workers.reassign_all()
    worker = workers.workers()[0]
    assert worker.assigned_building is camp
    # Lumberjack first walks to the camp; the chop cycle starts on arrival.
    assert worker.state == "moving"

    # 3) Advance simulated time: worker must move and eventually reach approach tile.
    start_tile = worker.current_tile
    workers.update(3000)
    mid_tile = worker.current_tile
    workers.update(120000)
    end_tile = worker.current_tile
    assert mid_tile != start_tile
    assert worker.state in {"chopping", "returning", "depositing", "going_to_tree"}
    assert world.is_in_grass(*end_tile)

    # 4) Production gating: Lumber Camp has no passive production in Phase 11.
    world2 = World()
    registry2 = BuildingRegistry(world2)
    registry2.place(TownHall, town_hall_origin_tile())
    camp2 = registry2.place(LumberCamp, near_town_hall_tile(14, 14))
    camp2.construction_site = None
    workers2 = WorkerManager(registry2)
    assert workers2.hire("LUMBERJACK") is not None
    workers2.reassign_all()
    th2 = next(b for b in registry2.all() if b.type_tag == "TOWN_HALL")
    wood_before = th2.warehouse_amount("wood")
    workers2.update(120_000)
    assert th2.warehouse_amount("wood") == wood_before

    # 5) Spacing rule: touching is rejected, one-tile gap is accepted.
    assert not registry.can_place(LumberCamp, (cgx + 2, cgy))
    assert registry.can_place(LumberCamp, (cgx + 3, cgy))
