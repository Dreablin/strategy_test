"""Mouse/keyboard routing: placement mode, building panel open/close (PRD F-INPUT / F-UI-PANEL)."""

from __future__ import annotations

import pygame

from game import dev_asset_reload
from game.buildings.bakery import Bakery
from game.buildings.base import Building
from game.buildings.canteen import Canteen
from game.buildings.chicken_farm import ChickenFarm
from game.buildings.cow_farm import CowFarm
from game.buildings.forester_hut import ForesterHut
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.mill import Mill
from game.buildings.stone_mine import StoneMine
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.sawmill import Sawmill
from game.buildings.town_hall import TownHall
from game.buildings.vineyard_farm import VineyardFarm
from game.buildings.well import Well
from game.camera import Camera
from game.iso import screen_to_tile
from game.render import Renderer
from game.housing import current_population, max_population
from game.ui.bottom_bar import BAR_HEIGHT, BUILD_MENU_SELECT, BottomBar
from game.ui.bakery_panel import BakeryPanel
from game.ui.canteen_panel import CanteenPanel
from game.ui.chicken_farm_panel import ChickenFarmPanel
from game.ui.cow_farm_panel import CowFarmPanel
from game.ui.building_panel import BuildingPanel
from game.ui.construction_panel import ConstructionPanel
from game.ui.forester_hut_panel import ForesterHutPanel
from game.ui.iron_mine_panel import IronMinePanel
from game.ui.lumber_camp_panel import LumberCampPanel
from game.ui.mill_panel import MillPanel
from game.ui.stone_mine_panel import StoneMinePanel
from game.ui.school_panel import SchoolPanel
from game.ui.sawmill_panel import SawmillPanel
from game.ui.placement import PlacementController
from game.ui.population_panel import PopulationPanel
from game.ui.town_hall_panel import TownHallPanel
from game.ui.top_bar import TopBar
from game.ui.vineyard_farm_panel import VineyardFarmPanel
from game.ui.well_panel import WellPanel
from game.ui.worker_panel import WorkerPanel
from game.world import World
from game.config import TILE_H, TILE_W
from game.iso import world_to_screen
from game.worker_geometry import building_center_tile
from game.worker_models import Worker
from game.workers import WorkerManager

# Matches `TopBar` strip; clicks above this are HUD, not map.
TOP_BAR_HEIGHT = 48


def screen_to_grid(
    surface: pygame.Surface,
    world: World,
    screen_pos: tuple[int, int],
    camera: Camera,
) -> tuple[int, int]:
    """Map screen pixel to isometric grid cell using the same origin as ``Renderer.draw_world``."""
    ox, oy = Renderer.map_origin(surface, world)
    mx, my = screen_pos
    return screen_to_tile(mx - camera.offset[0] - ox, my - camera.offset[1] - oy)


def _on_map(surface: pygame.Surface, pos: tuple[int, int]) -> bool:
    x, y = pos
    h = surface.get_height()
    return TOP_BAR_HEIGHT <= y < h - BAR_HEIGHT


class GameInput:
    """Owns building panel selection; delegates placement and bottom bar where appropriate."""

    __slots__ = (
        "_camera",
        "_panel",
        "_population_filter",
        "_population_panel_open",
        "_population_scroll",
        "_placement",
        "_registry",
        "_rmb_down",
        "_rmb_dragging",
        "_rmb_moved",
        "_rmb_press_pos",
        "_worker_manager",
        "_worker_panel",
        "_world",
    )

    def __init__(
        self,
        world: World,
        registry: BuildingRegistry,
        placement: PlacementController,
        worker_manager: WorkerManager,
        camera: Camera,
    ) -> None:
        self._world = world
        self._registry = registry
        self._placement = placement
        self._worker_manager = worker_manager
        self._camera = camera
        self._panel: Building | None = None
        self._worker_panel: Worker | None = None
        self._population_filter: str | None = None
        self._population_panel_open = False
        self._population_scroll = 0
        self._rmb_down = False
        self._rmb_dragging = False
        self._rmb_moved = False
        self._rmb_press_pos: tuple[int, int] = (0, 0)

    def _panel_worker_status(self) -> str:
        if self._panel is None:
            return "empty"
        return self._worker_manager.worker_status_for_building(self._panel)

    def _panel_production_status(self) -> str | None:
        if self._panel is None:
            return None
        return self._worker_manager.production_status_for_building(self._panel)

    def _sync_assignments(self) -> None:
        self._worker_manager.reassign_all()

    @property
    def panel_building(self) -> Building | None:
        """Building shown in the modal, or ``None`` if the panel is closed."""
        return self._panel

    @property
    def panel_worker(self) -> Worker | None:
        """Worker shown in the modal, or ``None`` if the panel is closed."""
        return self._worker_panel

    @property
    def population_panel_open(self) -> bool:
        """Whether the population list modal is open."""
        return self._population_panel_open

    @property
    def population_scroll(self) -> int:
        """Current population panel scroll offset in pixels."""
        return self._population_scroll

    @property
    def population_filter(self) -> str | None:
        """Current worker type filter in the population panel, or None for all."""
        return self._population_filter

    def _sync_panel_stale(self) -> None:
        if self._panel is not None and self._panel not in self._registry.all():
            self._panel = None
        if self._worker_panel is not None and self._worker_panel not in self._worker_manager.workers():
            self._worker_panel = None

    def _worker_screen_pos(self, surface: pygame.Surface, worker: Worker) -> tuple[int, int]:
        moving_states = {
            "moving",
            "going_to_tree",
            "going_to_stone",
            "going_to_plant_tile",
            "going_to_field",
            "going_to_vineyard",
            "returning",
        }
        if worker.state in moving_states and worker.target_tile is not None:
            cx, cy = worker.current_tile
            tx, ty = worker.target_tile
            t = max(0.0, min(1.0, worker.segment_progress))
            gx = cx + (tx - cx) * t
            gy = cy + (ty - cy) * t
        elif worker.assigned_building is not None and worker.state == "working":
            gx, gy = building_center_tile(worker.assigned_building)
        elif worker.assigned_building is not None:
            gx, gy = worker.current_tile
        else:
            gx, gy = worker.stand_tile
        ox, oy = Renderer.map_origin(surface, self._world)
        cam_x, cam_y = self._camera.offset
        sx, sy = world_to_screen(gx, gy)
        return ox + cam_x + sx + TILE_W // 2, oy + cam_y + sy + TILE_H // 2

    def _worker_at_screen(self, surface: pygame.Surface, pos: tuple[int, int]) -> Worker | None:
        best: tuple[int, float, Worker] | None = None
        px, py = pos
        for index, worker in enumerate(self._worker_manager.workers()):
            wx, wy = self._worker_screen_pos(surface, worker)
            dist_sq = float((px - wx) * (px - wx) + (py - wy) * (py - wy))
            if dist_sq > 20.0 * 20.0:
                continue
            depth = worker.current_tile[0] + worker.current_tile[1]
            candidate = (depth * 1000 + index, dist_sq, worker)
            if best is None or dist_sq < best[1] or (dist_sq == best[1] and candidate[0] > best[0]):
                best = candidate
        return None if best is None else best[2]

    def _center_camera_on_worker(self, surface: pygame.Surface, worker: Worker) -> None:
        wx, wy = self._worker_screen_pos(surface, worker)
        center_x = surface.get_width() // 2
        center_y = (TOP_BAR_HEIGHT + (surface.get_height() - BAR_HEIGHT)) // 2
        self._camera.pan(center_x - wx, center_y - wy)
        self._rmb_moved = True

    def consume_camera_moved(self) -> bool:
        moved = self._rmb_moved
        self._rmb_moved = False
        return moved

    def handle(self, surface: pygame.Surface, event: pygame.event.Event) -> None:
        self._sync_panel_stale()
        if event.type == BUILD_MENU_SELECT:
            self._panel = None
            self._worker_panel = None
            self._population_panel_open = False
            if event.building_type in {"DEV_TREE", "DEV_STONE", "DEV_IRON"}:
                self._placement.select_dev(event.building_type)
            else:
                self._placement.select(event.building_type)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._panel is not None or self._worker_panel is not None or self._population_panel_open:
                self._panel = None
                self._worker_panel = None
                self._population_panel_open = False
            else:
                self._placement.cancel()
            return
        if event.type == pygame.MOUSEWHEEL and self._population_panel_open:
            workers = self._worker_manager.workers()
            self._population_scroll = PopulationPanel.clamp_scroll(
                surface,
                workers,
                self._population_scroll - int(event.y) * 48,
                self._population_filter,
            )
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
            self._rmb_down = True
            self._rmb_dragging = False
            self._rmb_moved = False
            self._rmb_press_pos = event.pos
            return
        if event.type == pygame.MOUSEMOTION:
            if self._rmb_down:
                dx = event.pos[0] - self._rmb_press_pos[0]
                dy = event.pos[1] - self._rmb_press_pos[1]
                if max(abs(dx), abs(dy)) >= 4:
                    self._rmb_dragging = True
                if self._rmb_dragging:
                    rx, ry = event.rel
                    self._camera.pan(rx, ry)
                    self._rmb_moved = True
                return
            if _on_map(surface, event.pos):
                self._placement.update_hover(surface, event.pos, self._camera)
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_RIGHT:
            if not self._rmb_dragging:
                self._placement.cancel()
                self._panel = None
                self._worker_panel = None
                self._population_panel_open = False
            self._rmb_down = False
            self._rmb_dragging = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            if self._panel is not None or self._worker_panel is not None or self._population_panel_open:
                self._handle_map_left_click(surface, event.pos)
                return
            if not _on_map(surface, event.pos):
                if event.pos[1] < TOP_BAR_HEIGHT:
                    top_layout = TopBar.layout(
                        surface,
                        current_population=current_population(self._registry, self._worker_manager),
                        max_population=max_population(self._registry, self._worker_manager),
                        delivery_queue_size=self._worker_manager.transport_queue_size(),
                        active_delivery_count=self._worker_manager.active_transport_count(),
                    )
                    if top_layout.population_button.collidepoint(event.pos):
                        self._panel = None
                        self._worker_panel = None
                        self._population_panel_open = not self._population_panel_open
                        self._population_scroll = 0
                        self._population_filter = None
                        return
                if event.pos[1] < TOP_BAR_HEIGHT and dev_asset_reload.handle_click(surface, event.pos):
                    return
                if event.pos[1] >= surface.get_height() - BAR_HEIGHT:
                    BottomBar.handle_click(surface, event.pos)
                return
            self._handle_map_left_click(surface, event.pos)
            return

    def update_placement_hover(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        if _on_map(surface, pos):
            self._placement.update_hover(surface, pos, self._camera)

    def draw_panel(self, surface: pygame.Surface) -> None:
        self._sync_panel_stale()
        if self._population_panel_open:
            workers = self._worker_manager.workers()
            self._population_scroll = PopulationPanel.clamp_scroll(
                surface,
                workers,
                self._population_scroll,
                self._population_filter,
            )
            PopulationPanel.draw(surface, workers, self._population_scroll, self._population_filter)
            return
        if self._worker_panel is not None:
            WorkerPanel.draw(surface, self._worker_panel)
            return
        if self._panel is None:
            return
        if self._panel.is_under_construction:
            ConstructionPanel.draw(surface, self._panel, now_ms=pygame.time.get_ticks())
            return
        if self._panel.type_tag == "TOWN_HALL":
            assert isinstance(self._panel, TownHall)
            TownHallPanel.draw(
                surface,
                self._panel,
                worker_assigned=self._panel_worker_status() != "empty",
            )
            return
        if LumberCampPanel.supports_building(self._panel):
            assert isinstance(self._panel, LumberCamp)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            LumberCampPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                worker_working=worker_status == "assigned",
            )
            return
        if StoneMinePanel.supports_building(self._panel):
            assert isinstance(self._panel, StoneMine)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            StoneMinePanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                worker_working=worker_status == "assigned",
            )
            return
        if IronMinePanel.supports_building(self._panel):
            assert isinstance(self._panel, IronMine)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            IronMinePanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if ForesterHutPanel.supports_building(self._panel):
            assert isinstance(self._panel, ForesterHut)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            ForesterHutPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                worker_working=worker_status == "assigned",
            )
            return
        if SchoolPanel.supports_building(self._panel):
            assert isinstance(self._panel, School)
            worker_status = self._panel_worker_status()
            SchoolPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_manager=self._worker_manager,
            )
            return
        if SawmillPanel.supports_building(self._panel):
            assert isinstance(self._panel, Sawmill)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            SawmillPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if MillPanel.supports_building(self._panel):
            assert isinstance(self._panel, Mill)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            MillPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if BakeryPanel.supports_building(self._panel):
            assert isinstance(self._panel, Bakery)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            BakeryPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if CanteenPanel.supports_building(self._panel):
            assert isinstance(self._panel, Canteen)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            CanteenPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if ChickenFarmPanel.supports_building(self._panel):
            assert isinstance(self._panel, ChickenFarm)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            ChickenFarmPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if CowFarmPanel.supports_building(self._panel):
            assert isinstance(self._panel, CowFarm)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            CowFarmPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if WellPanel.supports_building(self._panel):
            assert isinstance(self._panel, Well)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            WellPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        if VineyardFarmPanel.supports_building(self._panel):
            assert isinstance(self._panel, VineyardFarm)
            worker_status = self._panel_worker_status()
            production_status = self._panel_production_status()
            VineyardFarmPanel.draw(
                surface,
                self._panel,
                worker_assigned=worker_status != "empty",
                worker_status=worker_status,
                production_status=production_status,
                now_ms=pygame.time.get_ticks(),
            )
            return
        worker_status = self._panel_worker_status()
        production_status = self._panel_production_status()
        BuildingPanel.draw(
            surface,
            self._panel,
            worker_assigned=worker_status != "empty",
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_status == "assigned",
        )

    def _handle_map_left_click(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        if self._placement.has_pending:
            if self._placement.try_place(surface, pos, self._camera):
                self._sync_assignments()
            return

        if self._population_panel_open:
            workers = self._worker_manager.workers()
            selected_worker = PopulationPanel.worker_at(surface, pos, workers, self._population_scroll, self._population_filter)
            if selected_worker is not None:
                self._center_camera_on_worker(surface, selected_worker)
                return
            action = PopulationPanel.click_action(surface, pos, workers, self._population_scroll, self._population_filter)
            if action == "close":
                self._population_panel_open = False
            elif action == "filter:all":
                self._population_filter = None
                self._population_scroll = 0
                return
            elif action is not None and action.startswith("filter:"):
                self._population_filter = action.removeprefix("filter:")
                self._population_scroll = 0
                return
            elif action == "inside":
                return
            else:
                self._population_panel_open = False

        if self._worker_panel is not None:
            layout = WorkerPanel.layout(surface, self._worker_panel)
            if layout.frame.collidepoint(pos):
                action = WorkerPanel.click_action(surface, pos, self._worker_panel)
                if action == "close":
                    self._worker_panel = None
                return
            self._worker_panel = None

        gx, gy = screen_to_grid(surface, self._world, pos, self._camera)

        if self._panel is not None:
            wa = self._panel_worker_status() != "empty"
            if self._panel.is_under_construction:
                layout = ConstructionPanel.layout(surface, self._panel)
                if layout.frame.collidepoint(pos):
                    action = ConstructionPanel.click_action(surface, pos, self._panel)
                    if action == "close":
                        self._panel = None
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    return
                self._panel = None
                return
            if self._panel.type_tag == "TOWN_HALL":
                assert isinstance(self._panel, TownHall)
                layout = TownHallPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                )
                action = None
                panel_hit = layout.frame.collidepoint(pos) or layout.storage_frame.collidepoint(pos)
                if panel_hit:
                    action = TownHallPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                    )
                if action == "close":
                    self._panel = None
                    return
                if action == "upgrade":
                    if self._registry.upgrade_building(self._panel):
                        self._sync_assignments()
                    return
                if panel_hit:
                    # Click inside Town Hall primary/secondary panels but on no actionable control.
                    return
                if action is not None and action.startswith("hire:"):
                    return
            if LumberCampPanel.supports_building(self._panel):
                assert isinstance(self._panel, LumberCamp)
                production_status = self._panel_production_status()
                layout = LumberCampPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = LumberCampPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                        self._sync_assignments()
                    return
            if StoneMinePanel.supports_building(self._panel):
                assert isinstance(self._panel, StoneMine)
                production_status = self._panel_production_status()
                layout = StoneMinePanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = StoneMinePanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                        self._sync_assignments()
                    return
            if IronMinePanel.supports_building(self._panel):
                assert isinstance(self._panel, IronMine)
                production_status = self._panel_production_status()
                layout = IronMinePanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = IronMinePanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    return
            if ForesterHutPanel.supports_building(self._panel):
                assert isinstance(self._panel, ForesterHut)
                production_status = self._panel_production_status()
                layout = ForesterHutPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = ForesterHutPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                        self._sync_assignments()
                    return
            if SchoolPanel.supports_building(self._panel):
                assert isinstance(self._panel, School)
                layout = SchoolPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                    worker_manager=self._worker_manager,
                )
                if layout.frame.collidepoint(pos):
                    action = SchoolPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                        worker_manager=self._worker_manager,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action is not None and action.startswith("hire:"):
                        worker_type = action.split(":", 1)[1]
                        now_fn = getattr(self._worker_manager, "_now_ms_fn", None)
                        now_ms = int(now_fn()) if callable(now_fn) else pygame.time.get_ticks()
                        self._panel.enqueue_training(worker_type, now_ms=now_ms)
                    elif action is not None and action.startswith("cancel:"):
                        slot_idx = int(action.split(":", 1)[1])
                        now_fn = getattr(self._worker_manager, "_now_ms_fn", None)
                        now_ms = int(now_fn()) if callable(now_fn) else pygame.time.get_ticks()
                        self._panel.cancel_training_at(slot_idx, now_ms=now_ms)
                    return
            if SawmillPanel.supports_building(self._panel):
                assert isinstance(self._panel, Sawmill)
                production_status = self._panel_production_status()
                layout = SawmillPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=wa,
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = SawmillPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=wa,
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                        self._sync_assignments()
                    return
            if MillPanel.supports_building(self._panel):
                assert isinstance(self._panel, Mill)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = MillPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = MillPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            if BakeryPanel.supports_building(self._panel):
                assert isinstance(self._panel, Bakery)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = BakeryPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = BakeryPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            if CanteenPanel.supports_building(self._panel):
                assert isinstance(self._panel, Canteen)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = CanteenPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = CanteenPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            if ChickenFarmPanel.supports_building(self._panel):
                assert isinstance(self._panel, ChickenFarm)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = ChickenFarmPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = ChickenFarmPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            if CowFarmPanel.supports_building(self._panel):
                assert isinstance(self._panel, CowFarm)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = CowFarmPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = CowFarmPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            if WellPanel.supports_building(self._panel):
                assert isinstance(self._panel, Well)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = WellPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = WellPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            if VineyardFarmPanel.supports_building(self._panel):
                assert isinstance(self._panel, VineyardFarm)
                worker_status = self._panel_worker_status()
                production_status = self._panel_production_status()
                layout = VineyardFarmPanel.layout(
                    surface,
                    self._panel,
                    worker_assigned=worker_status != "empty",
                    production_status=production_status,
                )
                if layout.frame.collidepoint(pos):
                    action = VineyardFarmPanel.click_action(
                        surface,
                        pos,
                        self._panel,
                        worker_assigned=worker_status != "empty",
                        production_status=production_status,
                    )
                    if action == "close":
                        self._panel = None
                    elif action == "upgrade" and self._panel is not None:
                        if self._registry.upgrade_building(self._panel):
                            self._sync_assignments()
                    elif action == "demolish" and self._panel is not None:
                        b = self._panel
                        self._registry.demolish(b, self._worker_manager)
                        self._panel = None
                        self._sync_assignments()
                    elif action == "toggle_active" and self._panel is not None:
                        self._panel.set_active(not self._panel.active)
                    return
            layout = BuildingPanel.layout(
                surface,
                self._panel,
                worker_assigned=wa,
                production_status=self._panel_production_status(),
            )
            if layout.frame.collidepoint(pos):
                action = BuildingPanel.click_action(
                    surface,
                    pos,
                    self._panel,
                    worker_assigned=wa,
                    production_status=self._panel_production_status(),
                )
                if action == "close":
                    self._panel = None
                elif action == "upgrade" and self._panel is not None:
                    if self._registry.upgrade_building(self._panel):
                        self._sync_assignments()
                elif action == "demolish" and self._panel is not None:
                    b = self._panel
                    self._registry.demolish(b, self._worker_manager)
                    self._panel = None
                    self._sync_assignments()
                return

            self._panel = None
            worker = self._worker_at_screen(surface, pos)
            if worker is not None:
                self._worker_panel = worker
                return
            target = self._registry.at(gx, gy)
            if target is not None:
                self._panel = target
            return

        worker = self._worker_at_screen(surface, pos)
        if worker is not None:
            self._worker_panel = worker
            return

        hit = self._registry.at(gx, gy)
        if hit is not None:
            # FIELD acts as a terrain/work tile; it does not open a building panel.
            if hit.type_tag != "FIELD":
                self._panel = hit
