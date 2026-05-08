"""GameInput: building panel open/close and map vs HUD routing."""

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.buildings.chicken_farm import ChickenFarm
from game.buildings.mill import Mill
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.sawmill import Sawmill
from game.buildings.town_hall import TownHall
from game.buildings.field import Field
from game.camera import Camera
from game.input import TOP_BAR_HEIGHT, GameInput, screen_to_grid
from game.render import Renderer
from game.ui.bottom_bar import BAR_HEIGHT, BUILD_MENU_SELECT
from game.ui.building_panel import BuildingPanel
from game.ui.construction_panel import ConstructionPanel
from game.ui.chicken_farm_panel import ChickenFarmPanel
from game.ui.lumber_camp_panel import LumberCampPanel
from game.ui.mill_panel import MillPanel
from game.ui.placement import PlacementController
from game.ui.population_panel import PopulationPanel
from game.ui.school_panel import SchoolPanel
from game.ui.sawmill_panel import SawmillPanel
from game.ui.top_bar import TopBar
from game.ui.worker_panel import WorkerPanel
from game.world import World
from game.workers import Worker, WorkerManager
from game.construction import ConstructionSite

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
    placement = PlacementController(world, registry)
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
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    pos = _tile_center(surface, world, *near_town_hall_tile())
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos))
    assert inp.panel_building is not None
    assert inp.panel_building.type_tag == "LUMBER_CAMP"


def test_map_click_opens_panel_for_worker() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    workers = WorkerManager(registry)
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    workers.add_worker(worker)
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, workers, camera)

    pos = _tile_center(surface, world, *near_town_hall_tile())
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos))

    assert inp.panel_worker is worker
    assert inp.panel_building is None


def test_map_click_prefers_worker_over_building_panel() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camera = Camera()
    workers = WorkerManager(registry)
    worker = Worker("LUMBERJACK", stand_tile=near_town_hall_tile())
    workers.add_worker(worker)
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, workers, camera)

    pos = _tile_center(surface, world, *camp.grid_pos)
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos))

    assert inp.panel_worker is worker
    assert inp.panel_building is None


def test_close_button_closes_worker_panel() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    workers = WorkerManager(registry)
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    workers.add_worker(worker)
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, workers, camera)

    inp.handle(
        surface,
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=_tile_center(surface, world, *near_town_hall_tile()),
        ),
    )
    assert inp.panel_worker is worker

    close = WorkerPanel.layout(surface, worker).close.center
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=close))

    assert inp.panel_worker is None
    assert inp.panel_building is None


def test_map_click_on_field_does_not_open_panel() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, (20, 20))
    field = registry.place(Field, (12, 10))
    field.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    pos = _tile_center(surface, world, 12, 10)

    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos),
    )

    assert inp.panel_building is None


def test_outside_panel_click_closes() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    b = inp.panel_building
    assert b is not None
    layout = BuildingPanel.layout(surface, b, worker_assigned=False)
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
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    b = registry.all()[0]
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    # The panel is a LumberCamp panel, which is drawn with extra_bottom_px to fit
    # the toggle row, so resolve the Close button against the matching layout.
    layout = LumberCampPanel.layout(surface, b, worker_assigned=False)
    cx, cy = layout.close.center
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=(cx, cy)))
    assert inp.panel_building is None


def test_escape_closes_panel() -> None:
    surface = pygame.Surface((640, 480))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
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
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="FARM"))
    assert inp.panel_building is None
    assert placement.pending_type is not None


def test_build_menu_select_sawmill_sets_pending_type() -> None:
    surface = pygame.Surface((640, 480))
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="SAWMILL"))
    assert placement.pending_type is not None
    assert placement.pending_type.type_tag == "SAWMILL"


def test_build_menu_select_mill_sets_pending_type() -> None:
    surface = pygame.Surface((640, 480))
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="MILL"))
    assert placement.pending_type is not None
    assert placement.pending_type.type_tag == "MILL"


def test_build_menu_select_chicken_farm_sets_pending_type() -> None:
    surface = pygame.Surface((640, 480))
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="CHICKEN_FARM"))
    assert placement.pending_type is not None
    assert placement.pending_type.type_tag == "CHICKEN_FARM"


def test_under_construction_building_uses_construction_panel_draw(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = camp  # noqa: SLF001 - direct panel setup for focused routing test
    calls = {"construction": 0, "lumber": 0}

    def _draw_construction(*args, **kwargs):
        calls["construction"] += 1

    def _draw_lumber(*args, **kwargs):
        calls["lumber"] += 1

    monkeypatch.setattr(ConstructionPanel, "draw", staticmethod(_draw_construction))
    monkeypatch.setattr(LumberCampPanel, "draw", staticmethod(_draw_lumber))

    inp.draw_panel(surface)

    assert calls["construction"] == 1
    assert calls["lumber"] == 0


def test_under_construction_panel_close_click_closes_without_demolish() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    pos = _tile_center(surface, world, *near_town_hall_tile())
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos))
    assert inp.panel_building is camp

    close_center = ConstructionPanel.layout(surface, camp).close.center
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=close_center))

    assert inp.panel_building is None
    assert camp in registry.all()


def test_under_construction_panel_demolish_click_removes_building() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = camp  # noqa: SLF001

    demolish_center = ConstructionPanel.layout(surface, camp).demolish.center
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=demolish_center))

    assert inp.panel_building is None
    assert camp not in registry.all()


def test_under_construction_click_outside_panel_does_not_hit_hidden_sawmill_buttons() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 8))
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = sawmill  # noqa: SLF001

    hidden_demolish_center = SawmillPanel.layout(
        surface,
        sawmill,
        worker_assigned=False,
        production_status="Under construction",
    ).demolish.center
    assert not ConstructionPanel.layout(surface, sawmill).frame.collidepoint(hidden_demolish_center)
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=hidden_demolish_center))

    assert inp.panel_building is None
    assert sawmill in registry.all()


def test_sawmill_panel_draw_routing(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 8))
    sawmill.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = sawmill  # noqa: SLF001
    called = {"sawmill": 0}

    def _draw_sawmill(*args, **kwargs):
        called["sawmill"] += 1

    monkeypatch.setattr(SawmillPanel, "draw", staticmethod(_draw_sawmill))
    inp.draw_panel(surface)
    assert called["sawmill"] == 1


def test_sawmill_panel_toggle_click_toggles_active() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    sawmill = registry.place(Sawmill, near_town_hall_tile(18, 8))
    sawmill.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = sawmill  # noqa: SLF001
    layout = SawmillPanel.layout(surface, sawmill, worker_assigned=False, production_status="No worker")
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.toggle.center),
    )
    assert sawmill.active is False


def test_mill_panel_draw_routing(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    mill = registry.place(Mill, near_town_hall_tile(20, 8))
    mill.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = mill  # noqa: SLF001
    called = {"mill": 0}

    def _draw_mill(*args, **kwargs):
        called["mill"] += 1

    monkeypatch.setattr(MillPanel, "draw", staticmethod(_draw_mill))
    inp.draw_panel(surface)
    assert called["mill"] == 1


def test_mill_panel_toggle_click_toggles_active() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    mill = registry.place(Mill, near_town_hall_tile(22, 8))
    mill.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = mill  # noqa: SLF001
    layout = MillPanel.layout(surface, mill, worker_assigned=False, production_status="No wheat")
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.toggle.center),
    )
    assert mill.active is False


def test_chicken_farm_panel_draw_routing(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(22, 8))
    farm.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = farm  # noqa: SLF001
    called = {"farm": 0}

    def _draw_farm(*args, **kwargs):
        called["farm"] += 1

    monkeypatch.setattr(ChickenFarmPanel, "draw", staticmethod(_draw_farm))
    inp.draw_panel(surface)
    assert called["farm"] == 1


def test_chicken_farm_panel_toggle_click_toggles_active() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(22, 8))
    farm.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)
    inp._panel = farm  # noqa: SLF001
    layout = ChickenFarmPanel.layout(surface, farm, worker_assigned=False, production_status="No grain")
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.toggle.center),
    )
    assert farm.active is False


def test_place_calls_reassign_all_and_assigns_idle_worker() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    workers.add_worker(Worker("LUMBERJACK"))
    inp = GameInput(world, registry, placement, workers, camera)
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="LUMBER_CAMP"))
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=_tile_center(surface, world, *near_town_hall_tile())),
    )
    all_b = registry.all()
    assert len(all_b) == 1
    placed = all_b[0]
    placed.construction_site = None
    workers.reassign_all()
    assert workers.is_staffed(placed)


def test_school_hire_button_calls_worker_manager_hire_and_spawns_at_school() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    camp = registry.place(LumberCamp, near_town_hall_tile(12, 12))
    camp.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)
    inp._panel = school
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    hire_button = next(rect for worker_type, rect in layout.hire_buttons if worker_type == "LUMBERJACK")
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=hire_button.center),
    )
    workers.update(30_000)
    assert len(workers.workers()) == 1
    hired = workers.workers()[0]
    sx, sy = school.grid_pos
    sw, sh = school.footprint
    assert hired.current_tile == (sx + sw // 2, sy + sh)
    assert workers.is_staffed(camp)


def test_hire_from_second_school_spawns_near_second_school() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school1 = registry.place(School, near_town_hall_tile(8, 8))
    school1.construction_site = None
    school2 = registry.place(School, near_town_hall_tile(18, 8))
    school2.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)

    inp._panel = school2
    layout = SchoolPanel.layout(surface, school2, worker_assigned=False)
    _, hire_button = layout.hire_buttons[0]
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=hire_button.center),
    )
    workers.update(30_000)

    assert len(workers.workers()) == 1
    hired = workers.workers()[0]
    s2x, s2y = school2.grid_pos
    s2w, s2h = school2.footprint
    assert hired.current_tile == (s2x + s2w // 2, s2y + s2h)


def test_school_enqueue_does_not_consume_wheat_or_spawn_instantly() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    town_hall.add_to_warehouse("wheat", 500)
    wheat_before = town_hall.warehouse_amount("wheat")
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)

    inp._panel = school
    layout = SchoolPanel.layout(surface, school, worker_assigned=False)
    _, hire_button = layout.hire_buttons[0]
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=hire_button.center),
    )
    assert len(workers.workers()) == 0
    assert town_hall.warehouse_amount("wheat") == wheat_before

    workers.update(29_999)
    assert len(workers.workers()) == 0
    workers.update(30_000)
    assert len(workers.workers()) == 1
    assert town_hall.warehouse_amount("wheat") == wheat_before


def test_school_panel_click_in_hud_area_is_handled_by_panel() -> None:
    surface = pygame.Surface((640, 240))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(12, 8))
    school.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)
    inp._panel = school  # noqa: SLF001
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, worker_manager=workers)
    forester_button = next(rect for worker_type, rect in layout.hire_buttons if worker_type == "FORESTER")
    assert forester_button.centery >= surface.get_height() - BAR_HEIGHT

    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=forester_button.center),
    )

    assert inp.panel_building is school
    assert school.training_queue()[-1].type_tag == "FORESTER"


def test_school_panel_can_enqueue_animal_herder_via_input_handler() -> None:
    surface = pygame.Surface((640, 240))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(12, 8))
    school.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)
    inp._panel = school  # noqa: SLF001
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, worker_manager=workers)
    herder_button = next(rect for worker_type, rect in layout.hire_buttons if worker_type == "ANIMAL_HERDER")
    assert herder_button.centery >= surface.get_height() - BAR_HEIGHT

    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=herder_button.center),
    )

    assert inp.panel_building is school
    assert school.training_queue()[-1].type_tag == "ANIMAL_HERDER"


def test_school_panel_upgrade_click_starts_upgrade_construction() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(12, 8))
    school.construction_site = None
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)
    inp._panel = school  # noqa: SLF001
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, worker_manager=workers)
    assert layout.upgrade is not None

    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.upgrade.center),
    )

    assert inp.panel_building is school
    assert school.is_under_construction
    assert school.construction_site is not None
    assert school.construction_site.target_level == 2


def test_school_panel_disabled_upgrade_click_does_not_start_construction() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(12, 8))
    school.construction_site = None
    assert school.enqueue_training("LUMBERJACK")
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, camera)
    inp._panel = school  # noqa: SLF001
    layout = SchoolPanel.layout(surface, school, worker_assigned=False, worker_manager=workers)
    assert layout.upgrade is not None
    assert layout.upgrade_enabled is False

    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.upgrade.center),
    )

    assert inp.panel_building is school
    assert school.construction_site is None


def test_dev_tools_place_entities_via_input_click() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(registry), camera)

    def _find_free_tile(start_x: int, start_y: int) -> tuple[int, int]:
        for dy in range(0, 12):
            for dx in range(0, 12):
                tx, ty = start_x + dx, start_y + dy
                if not world.is_in_grass(tx, ty):
                    continue
                if (
                    world.is_occupied(tx, ty)
                    or world.is_tree_blocking(tx, ty)
                    or world.is_stone_blocking(tx, ty)
                    or world.iron_deposit_at(tx, ty) is not None
                    or world.gold_deposit_at(tx, ty) is not None
                ):
                    continue
                return tx, ty
        raise AssertionError("No free tile found for dev tool placement")

    gx, gy = _find_free_tile(*near_town_hall_tile(2, 2))
    pos = _tile_center(surface, world, gx, gy)
    trees_before = len(world.iter_alive_trees())

    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_TREE"))
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos))
    assert len(world.iter_alive_trees()) == trees_before + 1

    gx2, gy2 = _find_free_tile(*near_town_hall_tile(5, 2))
    pos2 = _tile_center(surface, world, gx2, gy2)
    stones_before = len(world.iter_stones())
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_STONE"))
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos2))
    assert len(world.iter_stones()) == stones_before + 1

    gx3, gy3 = _find_free_tile(*near_town_hall_tile(8, 2))
    pos3 = _tile_center(surface, world, gx3, gy3)
    iron_before = len(world.iter_iron_deposits())
    inp.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="DEV_IRON"))
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=pos3))
    assert len(world.iter_iron_deposits()) == iron_before + 1
    placed_x, placed_y = placement.hover_grid  # type: ignore[misc]
    iron = world.iron_deposit_at(placed_x, placed_y)
    assert iron is not None
    assert iron.buildable


def test_top_bar_boundary_click_is_treated_as_map() -> None:
    """y == TOP_BAR_HEIGHT is considered map area for hover updates."""
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    placement.select("LUMBER_CAMP")
    inp.handle(surface, pygame.event.Event(pygame.MOUSEMOTION, pos=(100, TOP_BAR_HEIGHT), rel=(0, 0)))
    assert placement.hover_grid is not None


def test_population_button_opens_population_panel() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    workers.add_worker(Worker("CARRIER"))
    inp = GameInput(world, registry, placement, workers, camera)

    layout = TopBar.layout(surface, current_population=1, max_population=8)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.population_button.center),
    )

    assert inp.population_panel_open is True
    assert inp.panel_building is None
    assert inp.panel_worker is None


def test_population_panel_mousewheel_scrolls_when_many_workers() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    for _ in range(20):
        workers.add_worker(Worker("CARRIER"))
    inp = GameInput(world, registry, placement, workers, camera)

    layout = TopBar.layout(surface, current_population=20, max_population=20)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=layout.population_button.center),
    )
    assert inp.population_scroll == 0

    inp.handle(surface, pygame.event.Event(pygame.MOUSEWHEEL, y=-3))

    assert inp.population_panel_open is True
    assert inp.population_scroll > 0


def test_population_panel_absorbs_inside_clicks() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    workers.add_worker(Worker("CARRIER"))
    inp = GameInput(world, registry, placement, workers, camera)

    top_layout = TopBar.layout(surface, current_population=1, max_population=8)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=top_layout.population_button.center),
    )
    assert inp.population_panel_open is True

    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=surface.get_rect().center),
    )

    assert camp in registry.all()
    assert inp.population_panel_open is True
    assert inp.panel_building is None


def test_population_panel_worker_row_centers_camera_on_worker() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    worker = Worker("CARRIER", stand_tile=(4, 35))
    workers.add_worker(worker)
    inp = GameInput(world, registry, placement, workers, camera)

    top_layout = TopBar.layout(surface, current_population=1, max_population=8)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=top_layout.population_button.center),
    )
    panel_layout = PopulationPanel.layout(surface, workers.workers(), inp.population_scroll)
    row_click = (panel_layout.content.left + 24, panel_layout.content.top + 16)
    before = camera.offset

    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=row_click))

    assert camera.offset != before
    assert inp.population_panel_open is True
    assert inp.consume_camera_moved() is True
    sx, sy = world_to_screen(*worker.stand_tile)
    ox, oy = Renderer.map_origin(surface, world)
    worker_screen = (
        ox + camera.offset[0] + sx + TILE_W // 2,
        oy + camera.offset[1] + sy + TILE_H // 2,
    )
    assert worker_screen == (surface.get_width() // 2, (TOP_BAR_HEIGHT + surface.get_height() - BAR_HEIGHT) // 2)


def test_population_panel_filter_tile_limits_visible_workers() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    carrier = Worker("CARRIER", stand_tile=(4, 35))
    builder = Worker("BUILDER", stand_tile=(28, 35))
    workers.add_worker(carrier)
    workers.add_worker(builder)
    inp = GameInput(world, registry, placement, workers, camera)

    top_layout = TopBar.layout(surface, current_population=2, max_population=8)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=top_layout.population_button.center),
    )
    panel_layout = PopulationPanel.layout(surface, workers.workers(), inp.population_scroll, inp.population_filter)
    builder_filter = next(rect for worker_type, rect in panel_layout.filters if worker_type == "BUILDER")

    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=builder_filter.center))

    assert inp.population_filter == "BUILDER"
    filtered_layout = PopulationPanel.layout(surface, workers.workers(), inp.population_scroll, inp.population_filter)
    row_click = (filtered_layout.content.left + 24, filtered_layout.content.top + 16)
    before = camera.offset
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=row_click))

    assert camera.offset != before
    sx, sy = world_to_screen(*builder.stand_tile)
    ox, oy = Renderer.map_origin(surface, world)
    builder_screen = (
        ox + camera.offset[0] + sx + TILE_W // 2,
        oy + camera.offset[1] + sy + TILE_H // 2,
    )
    assert builder_screen == (surface.get_width() // 2, (TOP_BAR_HEIGHT + surface.get_height() - BAR_HEIGHT) // 2)


def test_population_panel_all_filter_restores_unfiltered_list() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    workers = WorkerManager(registry)
    workers.add_worker(Worker("CARRIER", stand_tile=(4, 35)))
    workers.add_worker(Worker("BUILDER", stand_tile=(28, 35)))
    inp = GameInput(world, registry, placement, workers, camera)

    top_layout = TopBar.layout(surface, current_population=2, max_population=8)
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=top_layout.population_button.center),
    )
    panel_layout = PopulationPanel.layout(surface, workers.workers(), inp.population_scroll, inp.population_filter)
    builder_filter = next(rect for worker_type, rect in panel_layout.filters if worker_type == "BUILDER")
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=builder_filter.center))
    assert inp.population_filter == "BUILDER"

    panel_layout = PopulationPanel.layout(surface, workers.workers(), inp.population_scroll, inp.population_filter)
    all_filter = next(rect for worker_type, rect in panel_layout.filters if worker_type is None)
    inp.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=all_filter.center))

    assert inp.population_filter is None


def test_bottom_bar_boundary_click_is_not_map() -> None:
    """y == (height - BAR_HEIGHT) belongs to HUD area and must not open map panel."""
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    registry.place(LumberCamp, near_town_hall_tile())
    camera = Camera()
    placement = PlacementController(world, registry, camera)
    inp = GameInput(world, registry, placement, WorkerManager(), camera)
    x, _ = _tile_center(surface, world, *near_town_hall_tile())
    hud_y = surface.get_height() - BAR_HEIGHT
    inp.handle(
        surface,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT, pos=(x, hud_y)),
    )
    assert inp.panel_building is None
