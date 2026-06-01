"""Town Hall panel UI: upgrade/close actions without hiring."""

import pygame

from game import i18n
from game.buildings.town_hall import TownHall
from game.resource_catalog import is_town_hall_warehouse_resource, resource_display_label
from game.ui import town_hall_panel
from game.ui.town_hall_panel import TownHallPanel


def test_town_hall_panel_layout_has_no_hire_buttons() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.hire_buttons == ()
    assert layout.upgrade is not None


def test_town_hall_panel_click_inside_without_buttons_returns_none() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    pos = (layout.frame.left + 20, layout.frame.bottom - 20)
    assert TownHallPanel.click_action(surface, pos, town_hall, worker_assigned=False) is None


def test_town_hall_panel_close_button_action() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert (
        TownHallPanel.click_action(surface, layout.close.center, town_hall, worker_assigned=False)
        == "close"
    )


def test_town_hall_panel_draw_smoke() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    TownHallPanel.draw(surface, town_hall, worker_assigned=False)
    assert surface.get_at((400, 300)) != (0, 0, 0, 255)


def test_hire_buttons_removed_from_town_hall_panel() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.hire_buttons == ()


def test_town_hall_panel_has_secondary_storage_frame_and_click_is_non_closing() -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.storage_frame.left > layout.frame.right
    assert (
        TownHallPanel.click_action(
            surface,
            layout.storage_frame.center,
            town_hall,
            worker_assigned=False,
        )
        is None
    )


def test_town_hall_storage_rows_include_bread_beef_hide_and_grapes() -> None:
    keys = [key for key, _label in town_hall_panel._STORAGE_ROWS]  # noqa: SLF001
    assert "bread" in keys
    assert "chicken" in keys
    assert "beef" in keys
    assert "hide" in keys
    assert "grapes" in keys
    beef_idx = keys.index("beef")
    assert town_hall_panel._STORAGE_ROWS[beef_idx][1] == resource_display_label("beef")  # noqa: SLF001
    hide_idx = keys.index("hide")
    assert town_hall_panel._STORAGE_ROWS[hide_idx][1] == resource_display_label("hide")  # noqa: SLF001
    grapes_idx = keys.index("grapes")
    assert town_hall_panel._STORAGE_ROWS[grapes_idx][1] == resource_display_label("grapes")  # noqa: SLF001


def test_beef_is_warehouse_resource_with_display_label() -> None:
    assert is_town_hall_warehouse_resource("beef")
    assert resource_display_label("beef") == i18n.t("resource.beef")


def test_hide_is_warehouse_resource_with_display_label() -> None:
    assert is_town_hall_warehouse_resource("hide")
    assert resource_display_label("hide") == i18n.t("resource.hide")


def test_grapes_is_warehouse_resource_with_display_label() -> None:
    assert is_town_hall_warehouse_resource("grapes")
    assert resource_display_label("grapes") == i18n.t("resource.grapes")


def test_town_hall_panel_draw_includes_beef_cell_with_quantity() -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    town_hall.add_to_warehouse("beef", 42)
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    before = surface.subsurface(layout.storage_frame).copy()
    TownHallPanel.draw(surface, town_hall, worker_assigned=False)
    after = surface.subsurface(layout.storage_frame).copy()
    assert before.get_bytesize() == after.get_bytesize()
    assert before.get_buffer().raw != after.get_buffer().raw


def test_town_hall_upgrade_tooltip_draws_above_storage(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    marker = layout.storage_frame.center

    def fake_tooltip(surface, building, upgrade_rect, *, hover_pos=None):
        surface.set_at(marker, (20, 240, 40))
        return pygame.Rect(marker[0], marker[1], 1, 1)

    monkeypatch.setattr(town_hall_panel, "draw_upgrade_cost_tooltip", fake_tooltip)

    TownHallPanel.draw(surface, town_hall, worker_assigned=False)

    assert surface.get_at(marker)[:3] == (20, 240, 40)


def test_town_hall_panel_draw_includes_hide_cell_with_quantity() -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    town_hall.add_to_warehouse("hide", 17)
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    before = surface.subsurface(layout.storage_frame).copy()
    TownHallPanel.draw(surface, town_hall, worker_assigned=False)
    after = surface.subsurface(layout.storage_frame).copy()
    assert before.get_bytesize() == after.get_bytesize()
    assert before.get_buffer().raw != after.get_buffer().raw


def test_town_hall_panel_draw_includes_grapes_cell_with_quantity() -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    town_hall.add_to_warehouse("grapes", 9)
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    before = surface.subsurface(layout.storage_frame).copy()
    TownHallPanel.draw(surface, town_hall, worker_assigned=False)
    after = surface.subsurface(layout.storage_frame).copy()
    assert before.get_bytesize() == after.get_bytesize()
    assert before.get_buffer().raw != after.get_buffer().raw


def test_wine_is_warehouse_resource_with_display_label() -> None:
    assert is_town_hall_warehouse_resource("wine")
    assert resource_display_label("wine") == i18n.t("resource.wine")


def test_town_hall_storage_rows_include_wine() -> None:
    keys = [key for key, _label in town_hall_panel._STORAGE_ROWS]  # noqa: SLF001
    assert "wine" in keys
    wine_idx = keys.index("wine")
    assert town_hall_panel._STORAGE_ROWS[wine_idx][1] == resource_display_label("wine")  # noqa: SLF001


def test_town_hall_warehouse_wine_default_zero_and_round_trip() -> None:
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    assert town_hall.warehouse_amount("wine") == 0
    town_hall.add_to_warehouse("wine", 5)
    assert town_hall.warehouse_amount("wine") == 5
    town_hall.take_from_warehouse("wine", 2)
    assert town_hall.warehouse_amount("wine") == 3


def test_town_hall_panel_draw_includes_wine_cell_with_quantity() -> None:
    surface = pygame.Surface((1280, 720))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    town_hall.add_to_warehouse("wine", 7)
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    before = surface.subsurface(layout.storage_frame).copy()
    TownHallPanel.draw(surface, town_hall, worker_assigned=False)
    after = surface.subsurface(layout.storage_frame).copy()
    assert before.get_bytesize() == after.get_bytesize()
    assert before.get_buffer().raw != after.get_buffer().raw


def test_town_hall_warehouse_title_ru(use_locale) -> None:
    with use_locale("ru"):
        assert i18n.t("ui.building.town_hall_warehouse") != "ui.building.town_hall_warehouse"
        assert resource_display_label("beef") == i18n.t("resource.beef")


def test_town_hall_upgrade_button_is_enabled_without_cost_checks() -> None:
    surface = pygame.Surface((800, 600))
    town_hall = TownHall(level=1, grid_pos=(10, 10))
    layout = TownHallPanel.layout(surface, town_hall, worker_assigned=False)
    assert layout.upgrade is not None
    assert layout.upgrade_enabled is True
