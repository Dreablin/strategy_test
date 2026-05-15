"""Shared worker timing and tuning constants."""

from game.config import building_int_setting

CHOP_DURATION_MS = 10_000
MINE_DURATION_MS = 10_000
PLANT_DURATION_MS = 5_000
LUMBERJACK_REST_MS = 5_000
STONECUTTER_REST_MS = 5_000
FORESTER_REST_MS = 5_000
FORESTER_TARGET_RANDOM_TRIES = 3
FORESTER_TARGET_RETRY_MS = 1_000
FORESTER_RETURN_RETRY_MS = 3_000
CARRIER_INTERACT_MS = 2_000
IRON_MINE_CYCLE_MS = building_int_setting("IRON_MINE", "production", "cycle_ms")
MINER_REST_MS = building_int_setting("IRON_MINE", "production", "rest_ms")
FARMER_REST_MS = 5_000
FARMER_ACTION_MS = 5_000
FARMER_FIELD_RADIUS = building_int_setting("FARM", "work_radius")
FORESTER_PLANT_RADIUS = building_int_setting("FORESTER_HUT", "plant_radius")
LUMBER_CAMP_RESOURCE_RADIUS = building_int_setting("LUMBER_CAMP", "resource_search_radius")
STONE_MINE_RESOURCE_RADIUS = building_int_setting("STONE_MINE", "resource_search_radius")
FARMER_NO_TARGET_WORKING_STATE_MS = 900_000
MOVE_SPEED_PER_LEVEL = 0.05
GATHER_SPEED_PER_LEVEL = 0.05
