"""Tests for construction site domain model (T186/T190)."""

from game.buildings.lumber_camp import LumberCamp
from game.construction import ConstructionSite
from game.workers import Worker


def test_remaining_resources_and_full_supply() -> None:
    site = ConstructionSite(
        required_resources={"wood": 3, "stone": 2},
        delivered_resources={"wood": 1},
        build_time_ms=30_000,
        build_started_ms=None,
        builder=None,
        target_level=2,
    )

    assert site.remaining_resources() == {"wood": 2, "stone": 2}
    assert site.is_fully_supplied() is False
    site.deliver_resource("stone", 2)
    site.deliver_resource("wood", 2)
    assert site.remaining_resources() == {"wood": 0, "stone": 0}
    assert site.is_fully_supplied() is True


def test_building_state_progress_and_completion() -> None:
    site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=3,
    )

    assert site.is_building() is False
    assert site.build_progress(5_000) == 0.0
    assert site.is_complete(5_000) is False

    site.build_started_ms = 1_000
    assert site.is_building() is True
    assert site.build_progress(1_000) == 0.0
    assert 0.49 <= site.build_progress(6_000) <= 0.51
    assert site.is_complete(10_999) is False
    assert site.is_complete(11_000) is True
    assert site.build_progress(12_000) == 1.0


def test_deliver_resource_is_capped_and_rejects_negative_amount() -> None:
    site = ConstructionSite(
        required_resources={"boards": 4},
        delivered_resources={},
        build_time_ms=20_000,
        build_started_ms=None,
        builder=None,
        target_level=4,
    )
    site.deliver_resource("boards", 10)
    assert site.delivered_resources["boards"] == 4
    site.deliver_resource("iron", 1)
    assert site.delivered_resources["iron"] == 0

    try:
        site.deliver_resource("boards", -1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for negative delivery amount")


def test_complete_construction_finishes_initial_building_site() -> None:
    from game.construction import complete_construction

    building = LumberCamp(level=1, grid_pos=(10, 10))
    building.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=5_000,
        build_started_ms=100,
        builder=None,
        target_level=1,
    )

    assert complete_construction(building, now_ms=5_099) is False
    assert complete_construction(building, now_ms=5_100) is True
    assert building.level == 1
    assert building.construction_site is None
    assert building.is_under_construction is False


def test_complete_construction_finishes_upgrade_releases_builder_and_restores_worker() -> None:
    from game.construction import complete_construction

    building = LumberCamp(level=1, grid_pos=(10, 10))
    building.active = False
    builder = Worker("BUILDER")
    builder.assigned_building = building
    builder.idle = False
    builder.state = "building"

    resting = Worker("LUMBERJACK")
    resting.assigned_building = building
    resting.idle = False
    resting.state = "resting"

    building.construction_site = ConstructionSite(
        required_resources={"wood": 4},
        delivered_resources={"wood": 4},
        build_time_ms=3_000,
        build_started_ms=1_000,
        builder=builder,
        target_level=2,
        resting_worker=resting,
    )

    assert complete_construction(building, now_ms=4_000) is True
    assert building.level == 2
    assert building.construction_site is None
    assert building.active is True

    assert builder.idle is True
    assert builder.state == "idle"
    assert builder.assigned_building is None

    assert resting.assigned_building is building
    assert resting.idle is False
    assert resting.state == "working"
