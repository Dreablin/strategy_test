"""GameInput: building panel open/close and map vs HUD routing."""

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.input import TOP_BAR_HEIGHT, GameInput, screen_to_grid
from game.render import Renderer
from game.resources import ResourceManager
from game.ui.bottom_bar import BAR_HEIGHT, BUILD_MENU_SELECT
from game.ui.building_panel import BuildingPanel
from game.ui.lumber_camp_panel import LumberCampPanel
from game.ui.placement import PlacementController
from game.ui.town_hall_panel import TownHallPanel
from game.world import World
from game.workers import Worker, WorkerManager

from game.config import TILE_H, TILE_W, near_town_hall_tile, town_hall_origin_tile
from game.iso import world_to_screen


def _tile_center(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + TILE_W // 2, oy + sy + TILE_H // 2


def test_screen_to_grid_matches_placement_hover() -> None:
    """Same origin and projection as ``PlacementController.update_hover``."""
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    placement = PlacementController(world, registry, resources)
    camera = Camera()
    placement.select("LUMBER_CAMP")
    pos = (523, 381)
    placement.update_hover(surface, pos)
    assert placement.hover_grid is not None
    assert screen_to_grid(surface, world, pos, camera) == placement.hover_grid


def test_map_click_opens_panel_for_building() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    pos = _tile_center(surface, world, *near_town_hall_tile())
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos))
    assert inp.panel_building is not None
    assert inp.panel_building.type_tag == "LUMBER_CAMP"


def test_outside_panel_click_closes() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    b = inp.panel_building
    assert b is not None
    layout = BuildingPanel.layout(surface, b, resources, worker_assigned=False)
    pos_out: tuple[int, int] | None = None
    for my in range(TOP_BAR_HEIGHT + 40, surface.get_height() - BAR_HEIGHT - 8, 15):
        for mx in range(40, layout.frame.left - 8, 4):
            if not layout.frame.collidepoint(mx, my):
                gx, gy = screen_to_grid(surface, world, (mx, my), camera)
                if registry.at(gx, gy) is None:
                    pos_out = (mx, my)
                    break
        if pos_out is not None:
            break
    assert pos_out is not None
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos_out))
    assert inp.panel_building is None


def test_close_button_closes_panel() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    b = registry.all()[0]
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    # The panel is a LumberCamp panel, which is drawn with extra_bottom_px to fit
    # the toggle row, so resolve the Close button against the matching layout.
    layout = LumberCampPanel.layout(surface, b, resources, worker_assigned=False)
    cx, cy = layout.close.center
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=(cx, cy)))
    assert inp.panel_building is None


def test_escape_closes_panel() -> None:
    surface = pygame.Surface((640, 480))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    inp.handle(surface, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert inp.panel_building is None


def test_build_menu_select_closes_panel() -> None:
    surface = pygame.Surface((640, 480))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="FARM"))
    assert inp.panel_building is None
    assert placement.pending_type is not None


def test_place_calls_reassign_all_and_assigns_idle_worker() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    workers = WorkerManager(resources, registry)
    workers.add_worker(Worker("LUMBERJACK"))
    inp = GameInput(world, registry, resources, placement, workers, camera)
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="LUMBER_CAMP"))
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    all_b = registry.all()
    assert len(all_b) == 1
    placed = all_b[0]
    assert workers.is_staffed(placed)


def test_town_hall_hire_button_calls_worker_manager_hire() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(12, 12))
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    workers = WorkerManager(resources, registry)
    inp = GameInput(world, registry, resources, placement, workers, camera)
    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=_tile_center(
                surface,
                world,
                town_hall_origin_tile()[0] + 1,
                town_hall_origin_tile()[1] + 1,
            ),
        ),
    )
    layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=False)
    _, hire_button = layout.hire_buttons[0]
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=hire_button.center),
    )
    assert len(workers.workers()) == 1
    assert workers.is_staffed(camp)


def test_top_bar_boundary_click_is_treated_as_map() -> None:
    """y == TOP_BAR_HEIGHT is considered map area for hover updates."""
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    placement.select("LUMBER_CAMP")
    inp.handle(surface, pygame.event.Event(pygame.MOUSEMOTION, pos=(100, TOP_BAR_HEIGHT), rel=(0, 0)))
    assert placement.hover_grid is not None


def test_bottom_bar_boundary_click_is_not_map() -> None:
    """y == (height - BAR_HEIGHT) belongs to HUD area and must not open map panel."""
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    resources = ResourceManager()
    camera = Camera()
    placement = PlacementController(world, registry, resources, camera)
    inp = GameInput(world, registry, resources, placement, WorkerManager(), camera)
    x, _ = _tile_center(surface, world, *near_town_hall_tile())
    hud_y = surface.get_height() - BAR_HEIGHT
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=(x, hud_y)),
    )
    assert inp.panel_building is None
