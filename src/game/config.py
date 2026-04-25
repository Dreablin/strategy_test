"""Global game configuration constants."""

TICK_MS = 10_000
TILE_W = 64
TILE_H = 32
GRID_SIZE = 32

INITIAL_RESOURCES = {
    "food": 200,
    "wood": 200,
    "stone": 0,
    "iron": 0,
}

WORKER_HIRE_COST = {"food": 50}
BUILD_COST_WOOD = 100
MAX_LEVEL = 10

WINDOW_SIZE = (1280, 720)
