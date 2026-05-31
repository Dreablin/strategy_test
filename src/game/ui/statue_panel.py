"""Statue panel wrapper: stage-aware upgrade, no demolition."""

from __future__ import annotations

import pygame

from game.buildings.statue import Statue
from game.research_state import ResearchState
from game.statue_research import statue_stage_unlocked
from game.ui.building_panel import BuildingPanel


class StatuePanel:
    @staticmethod
    def supports_building(building: object) -> bool:
        return isinstance(building, Statue)

    @staticmethod
    def _upgrade_research_unlocked(statue: Statue, research_state: ResearchState | None) -> bool:
        return statue_stage_unlocked(research_state, int(statue.level) + 1)

    @staticmethod
    def layout(
        surface: pygame.Surface,
        statue: Statue,
        *,
        research_state: ResearchState | None = None,
    ):
        return BuildingPanel.layout(
            surface,
            statue,
            worker_assigned=False,
            show_demolish=False,
            upgrade_enabled_override=StatuePanel._upgrade_research_unlocked(statue, research_state),
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        statue: Statue,
        *,
        research_state: ResearchState | None = None,
    ) -> None:
        BuildingPanel.draw(
            surface,
            statue,
            worker_assigned=False,
            worker_status="empty",
            show_demolish=False,
            upgrade_enabled_override=StatuePanel._upgrade_research_unlocked(statue, research_state),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        statue: Statue,
        *,
        research_state: ResearchState | None = None,
    ) -> str | None:
        return BuildingPanel.click_action(
            surface,
            pos,
            statue,
            worker_assigned=False,
            show_demolish=False,
            upgrade_enabled_override=StatuePanel._upgrade_research_unlocked(statue, research_state),
        )
