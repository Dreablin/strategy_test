"""Shared worker timing and tuning constants."""

from game.config import building_int_setting

CHOP_DURATION_MS = building_int_setting("LUMBER_CAMP", "work", "action_ms")
MINE_DURATION_MS = building_int_setting("STONE_MINE", "work", "action_ms")
PLANT_DURATION_MS = building_int_setting("FORESTER_HUT", "work", "action_ms")
LUMBERJACK_REST_MS = building_int_setting("LUMBER_CAMP", "work", "rest_ms")
STONECUTTER_REST_MS = building_int_setting("STONE_MINE", "work", "rest_ms")
FORESTER_REST_MS = building_int_setting("FORESTER_HUT", "work", "rest_ms")
FORESTER_TARGET_RANDOM_TRIES = 3
FORESTER_TARGET_RETRY_MS = 1_000
FORESTER_RETURN_RETRY_MS = 3_000
CARRIER_INTERACT_MS = 2_000
IRON_MINE_CYCLE_MS = building_int_setting("IRON_MINE", "production", "cycle_ms")
MINER_REST_MS = building_int_setting("IRON_MINE", "production", "rest_ms")
FARMER_REST_MS = building_int_setting("FARM", "work", "rest_ms")
FARMER_ACTION_MS = building_int_setting("FARM", "work", "action_ms")
FARMER_FIELD_RADIUS = building_int_setting("FARM", "work_radius")
FORESTER_PLANT_RADIUS = building_int_setting("FORESTER_HUT", "plant_radius")
LUMBER_CAMP_RESOURCE_RADIUS = building_int_setting("LUMBER_CAMP", "resource_search_radius")
STONE_MINE_RESOURCE_RADIUS = building_int_setting("STONE_MINE", "resource_search_radius")
FARMER_NO_TARGET_WORKING_STATE_MS = 900_000
MOVE_SPEED_PER_LEVEL = 0.05
GATHER_SPEED_PER_LEVEL = 0.05


def worker_building_action_ms(type_tag: str) -> int:
    return building_int_setting(type_tag, "work", "action_ms")


def worker_building_rest_ms(type_tag: str) -> int:
    return building_int_setting(type_tag, "work", "rest_ms")
