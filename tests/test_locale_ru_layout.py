"""RU locale layout overflow checks (T465)."""

from __future__ import annotations

import pygame

from game import i18n
from game.buildings.laboratory import Laboratory
from game.buildings.lumber_camp import LumberCamp
from game.buildings.town_hall import TownHall
from game.buildings.vineyard_farm import VineyardFarm
from game.construction import ConstructionSite
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_config import RESEARCH_BY_ID
from game.ui.bottom_bar import (
    _FOOD_BUTTON_SPECS,
    _PROCESSING_BUILDING_TAGS,
    _RESOURCE_BUTTON_SPECS,
    _SOCIAL_BUILDING_TAGS,
    _button_rects,
    _fit_bar_label,
    _main_menu_entries,
)
from game.ui.building_panel import (
    BuildingPanel,
    _CLOSE as BUILDING_CLOSE,
    _PANEL_PAD as BUILDING_PAD,
    _PANEL_W as BUILDING_W,
    _upgrade_label,
    building_display_name,
)
from game.ui.construction_panel import ConstructionPanel
from game.ui.fonts import render_fitted_ui_text, ui_font
from game.ui.research_screen import ResearchScreen
from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_start_button import start_button_label
from game.ui.research_tile_layout import compute_research_tile_layouts
from game.ui.worker_labels import worker_display_label
from game.ui.worker_panel import WorkerPanel, _CLOSE as WORKER_CLOSE, _PANEL_PAD as WORKER_PAD, _PANEL_W as WORKER_W
from game.worker_models import TransportTask, Worker

_SURFACE = (1280, 720)
_SCREEN_PAD = 16
_RESEARCH_CLOSE = 28


def _text_width(text: str, size: int) -> int:
    return ui_font(size).render(text, True, (255, 255, 255)).get_width()


def _assert_fitted(text: str, max_width: int, *, sizes: tuple[int, ...] = (28, 24, 22, 20, 18, 16)) -> None:
    surf = render_fitted_ui_text(text, max_width, sizes=sizes)
    assert surf.get_width() <= max_width, f"{text!r} still {surf.get_width()}px wide (max {max_width})"


def _assert_fits(text: str, font_size: int, max_width: int) -> None:
    width = _text_width(text, font_size)
    assert width <= max_width, f"{text!r} is {width}px wide at {font_size}pt (max {max_width})"


def _title_max(panel_w: int, pad: int, close: int) -> int:
    return panel_w - 2 * pad - close - 4


def _content_max(panel_w: int, pad: int) -> int:
    return panel_w - 2 * pad


def _bar_btn_width(surface: pygame.Surface, count: int) -> int:
    rect = _button_rects(surface, count)[0]
    return rect.inflate(-6, -10).width


def test_bottom_bar_main_categories_fit_ru(use_locale) -> None:
    surface = pygame.Surface(_SURFACE)
    with use_locale("ru"):
        max_w = _bar_btn_width(surface, len(_main_menu_entries()))
        for _key, label in _main_menu_entries():
            surf = _fit_bar_label(label, max_w)
            assert surf.get_width() <= max_w


def test_bottom_bar_building_submenus_fit_ru(use_locale) -> None:
    surface = pygame.Surface(_SURFACE)
    with use_locale("ru"):
        cases = (
            (len(_RESOURCE_BUTTON_SPECS) + 1, [building_display_name(tag) for _, tag in _RESOURCE_BUTTON_SPECS]),
            (len(_FOOD_BUTTON_SPECS) + 1, [building_display_name(tag) for _, tag in _FOOD_BUTTON_SPECS]),
            (
                len(_SOCIAL_BUILDING_TAGS) + 1,
                [building_display_name(tag) for tag in _SOCIAL_BUILDING_TAGS],
            ),
            (
                len(_PROCESSING_BUILDING_TAGS) + 1,
                [building_display_name(tag) for tag in _PROCESSING_BUILDING_TAGS],
            ),
        )
        for count, labels in cases:
            max_w = _bar_btn_width(surface, count)
            for label in labels:
                assert _fit_bar_label(label, max_w).get_width() <= max_w


def test_building_panel_ru_text_fits(use_locale) -> None:
    surface = pygame.Surface(_SURFACE)
    title_max = _title_max(BUILDING_W, BUILDING_PAD, BUILDING_CLOSE)
    body_max = _content_max(BUILDING_W, BUILDING_PAD)
    with use_locale("ru"):
        for building in (
            LumberCamp(level=3, grid_pos=(10, 10)),
            VineyardFarm(level=2, grid_pos=(12, 12)),
            Laboratory(level=2, grid_pos=(14, 14)),
        ):
            name = building_display_name(building.type_tag)
            title = i18n.t("ui.building.panel_title", name=name, level=building.level)
            _assert_fitted(title, title_max)
            layout = BuildingPanel.layout(surface, building, worker_assigned=True, production_status="working")
            if layout.upgrade is not None:
                _assert_fits(_upgrade_label(building), 24, layout.upgrade.width)
            if layout.demolish is not None:
                _assert_fits(i18n.t("ui.button.demolish"), 24, layout.demolish.width)
        lumber = LumberCamp(level=3, grid_pos=(10, 10))
        _assert_fits(BuildingPanel.storage_line(lumber), 22, body_max)


def test_worker_panel_ru_body_lines_fit(use_locale) -> None:
    th = TownHall(level=1, grid_pos=town_hall_origin_tile())
    vf = VineyardFarm(level=2, grid_pos=near_town_hall_tile(12, 8))
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.transport_task = TransportTask(
        resource="grapes",
        source=vf,
        target=th,
        purpose="generic",
        returning_to_town_hall=True,
    )
    worker.state = "moving"
    worker.carrying = "grapes"
    worker.assigned_building = vf
    worker.satiety = 4321
    with use_locale("ru"):
        title_max = _title_max(WORKER_W, WORKER_PAD, WORKER_CLOSE)
        _assert_fits(worker_display_label(worker.type_tag), 28, title_max)
        body_max = _content_max(WORKER_W, WORKER_PAD)
        for line in WorkerPanel.body_lines(worker):
            _assert_fits(line, 22, body_max)


def test_research_screen_ru_labels_fit(use_locale) -> None:
    surface = pygame.Surface(_SURFACE)
    with use_locale("ru"):
        title_max = surface.get_width() - _SCREEN_PAD - _RESEARCH_CLOSE - _SCREEN_PAD - 8
        _assert_fitted(ResearchScreen.screen_title(), title_max, sizes=(36, 32, 28, 24))
        _assert_fitted(ResearchScreen.technology_label(), 120, sizes=(20, 18, 16))
        content = compute_content_layout(surface)
        for row in content.tier_rows:
            _assert_fits(ResearchScreen.tier_label(row.tier), 20, row.row_rect.width - row.technology_slot.width - 24)
        for tile in compute_research_tile_layouts(content):
            entry = RESEARCH_BY_ID[tile.research_id]
            _assert_fits(entry.name, 18, tile.title_rect.width)
            _assert_fits(start_button_label(), 20, tile.start_button.width)


def test_construction_panel_ru_text_fits(use_locale) -> None:
    from game.ui.construction_panel import _CLOSE, _PANEL_PAD, _PANEL_W

    surface = pygame.Surface(_SURFACE)
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 10, "stone": 5, "iron": 3},
        delivered_resources={"wood": 4, "stone": 1, "iron": 0},
        build_time_ms=10_000,
        build_started_ms=0,
        builder=None,
        target_level=2,
    )
    title_max = _title_max(_PANEL_W, _PANEL_PAD, _CLOSE)
    body_max = _content_max(_PANEL_W, _PANEL_PAD)
    resource_max = body_max - 24
    with use_locale("ru"):
        name = building_display_name(camp.type_tag)
        title = f"{name} — {ConstructionPanel.title_line(camp)}"
        _assert_fitted(title, title_max)
        layout = ConstructionPanel.layout(surface, camp)
        _assert_fits(i18n.t("ui.common.requirements_colon"), 22, body_max)
        for resource, required in camp.construction_site.required_resources.items():
            delivered = int(camp.construction_site.delivered_resources.get(resource, 0))
            line = ConstructionPanel.resource_delivery_line(resource, delivered, int(required))
            _assert_fits(line, 20, resource_max)
        builder_line = i18n.t(
            "ui.construction.builder",
            status=ConstructionPanel.builder_status(camp),
        )
        _assert_fits(builder_line, 22, body_max)
        _assert_fits(i18n.t("ui.construction.progress", pct=50), 22, body_max)
        if layout.demolish is not None:
            _assert_fits(i18n.t("ui.button.demolish"), 24, layout.demolish.width)
