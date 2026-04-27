# PRD — Isometric Economy Strategy Game

## 1. Overview

### Problem
A standalone, lightweight isometric economy strategy game playable on Windows 11
without any prerequisite installation. The player builds a town, harvests four
resources (food, wood, stone, iron), hires workers, and upgrades buildings.

### Solution
A self-contained Python game packaged with PyInstaller into a single `.exe`.
Pure 2D isometric rendering done with Pygame primitives — no external assets,
no game engine, no save/load, no main menu. Game starts immediately and runs
until the player closes the window, releasing all OS resources cleanly.

### Target user
A solo player on Windows 11 who wants a simple, focused economy-builder
session (5–30 minutes) with no installation friction.

---

## 2. Technology Stack

| Component                | Technology              | Rationale                                                 |
|--------------------------|-------------------------|-----------------------------------------------------------|
| Language                 | Python 3.12             | Fast iteration, rich stdlib, easy to test                 |
| Rendering / Input        | pygame 2.5.2            | Mature 2D library, single dependency, MIT-friendly        |
| Tests                    | pytest 8.x              | Standard, fast, supports headless via `SDL_VIDEODRIVER`   |
| Packaging                | PyInstaller 6.x         | Produces single Windows `.exe`, no install required       |
| Lint / Format (optional) | ruff                    | Single tool, fast                                         |
| Assets                   | Procedural (Pygame draw)| No binary files; reproducible; ralph-loop friendly        |

### Project directory tree

```
game/
├── PRD.md                       # this file (read-only for agent)
├── prompt.md                    # ralph turn prompt
├── progress.md                  # task tracker (agent's persistent memory)
├── README.md                    # how to run / build
├── requirements.txt             # runtime + dev dependencies
├── pyproject.toml               # pytest + ruff config
├── build_exe.bat                # PyInstaller one-shot script
├── game.spec                    # PyInstaller spec (generated/edited)
├── .gitignore
├── .cursor/
│   └── rules/
│       ├── ralph-loop.mdc
│       └── python.mdc
├── src/
│   └── game/
│       ├── __init__.py
│       ├── main.py              # entry point: pygame window, game loop
│       ├── config.py            # all constants
│       ├── iso.py               # world ↔ screen isometric transforms
│       ├── assets.py            # procedural sprite/icon factory
│       ├── resources.py         # ResourceManager (food/wood/stone/iron)
│       ├── world.py             # grid, occupancy, grass/tree zones
│       ├── tick.py              # 10-second cycle scheduler
│       ├── buildings/
│       │   ├── __init__.py
│       │   ├── base.py          # Building base class
│       │   ├── town_hall.py
│       │   ├── lumber_camp.py
│       │   ├── stone_mine.py
│       │   ├── iron_mine.py
│       │   ├── farm.py
│       │   ├── costs.py         # upgrade-cost formulas
│       │   └── registry.py      # BuildingRegistry, placement validation
│       ├── workers.py           # Worker, WorkerManager, assignment
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── top_bar.py       # resources + per-cycle income
│       │   ├── bottom_bar.py    # building selection menu
│       │   ├── placement.py     # mouse-follow contour, click to place
│       │   ├── building_panel.py# modal: info / demolish / upgrade
│       │   └── town_hall_panel.py # extends building_panel: hire workers
│       ├── render.py            # main scene renderer
│       └── input.py             # mouse/keyboard event router
└── tests/
    ├── __init__.py
    ├── conftest.py              # SDL_VIDEODRIVER=dummy, fixtures
    ├── test_config.py
    ├── test_iso.py
    ├── test_resources.py
    ├── test_world.py
    ├── test_costs.py
    ├── test_buildings.py
    ├── test_registry.py
    ├── test_workers.py
    ├── test_tick.py
    └── test_production.py
```

---

## 3. Functional Requirements

### F-WIN — Window & Lifecycle

- **F-WIN-01 (MUST):** On launch, open a single 1280×720 (or larger if monitor is bigger; never larger than primary monitor) windowed pygame window titled `"Isometric Strategy"`. Game starts immediately — no menus.
- **F-WIN-02 (MUST):** The game loop runs at 60 FPS with `pygame.time.Clock`.
- **F-WIN-03 (MUST):** When the player closes the window (X button, Alt-F4, or `pygame.QUIT` event), `pygame.quit()` is called, all worker threads (if any) are joined, and the process exits with code `0`. No background processes remain.

### F-RES — Resources

- **F-RES-01 (MUST):** Track 4 resources: `food`, `wood`, `stone`, `iron`. All non-negative integers.
- **F-RES-02 (MUST):** Initial values: `food=200`, `wood=200`, `stone=0`, `iron=0`.
- **F-RES-03 (MUST):** ResourceManager exposes `get(name)`, `add(name, n)`, `try_spend(cost: dict) -> bool`, `has(cost: dict) -> bool`.
- **F-RES-04 (MUST):** Per-cycle income (computed from active buildings + workers) is exposed for UI as a dict.

```python
class ResourceManager:
    def get(self, name: str) -> int: ...
    def add(self, name: str, amount: int) -> None: ...
    def has(self, cost: Mapping[str, int]) -> bool: ...
    def try_spend(self, cost: Mapping[str, int]) -> bool: ...
    @property
    def per_cycle(self) -> dict[str, int]: ...
```

### F-TICK — Cycle System

- **F-TICK-01 (MUST):** A cycle lasts exactly **10 seconds** of wall-clock game time (using `pygame.time.get_ticks()`).
- **F-TICK-02 (MUST):** On each cycle tick, every working building (with assigned worker) produces `5 × level` units of its resource, added atomically.

### F-ISO — Isometric Projection

- **F-ISO-01 (MUST):** Tile size 64×32 (classic 2:1 diamond). No zoom, no rotation. Camera **pan via RMB drag** is supported (see F-CAM).
- **F-ISO-02 (MUST):** `iso.world_to_screen(gx, gy)` and `iso.screen_to_world(px, py)` are inverses (rounded to int grid). They operate in *world* pixels; camera offset is applied separately by the renderer.

### F-CAM — Camera Pan

- **F-CAM-01 (MUST):** A `Camera` carries an integer `offset = (ox, oy)` in pixels, initially `(0, 0)`.
- **F-CAM-02 (MUST):** `Renderer.draw_world`, `draw_buildings`, `draw_workers` and the placement preview apply `camera.offset` before blitting. `TopBar`, `BottomBar` and modal panels are drawn in **screen** coordinates and DO NOT pan.
- **F-CAM-03 (MUST):** `screen_to_grid` subtracts `camera.offset` before calling `iso.screen_to_world`, so clicks land on the correct world tile when panned.
- **F-CAM-04 (MUST):** `camera.clamp(viewport_size, world_bounds_px)` keeps the world's bounding box (grass + tree skirt) inside the viewport play area (between TopBar and BottomBar). When the world is bigger than the viewport, only previously off-screen parts can be revealed; when smaller, the offset is locked at the centering value.
- **F-CAM-05 (MUST):** Camera UX = **"grab-and-drag the world"**: if the mouse moves by `(dx, dy)` while RMB is held, then `camera.offset += (dx, dy)` (the world moves with the cursor), then immediately clamped per F-CAM-04.

### F-WORLD — World

- **F-WORLD-01 (MUST):** A `GRID_SIZE × GRID_SIZE` tile playable grass field (currently 55×55 in `game_settings.json`), centered on screen. Camera pan is required to see the whole map.
- **F-WORLD-02 (MUST, **revised**):** Trees are world-owned entities (Phase 10) that block movement and can be chopped (Phase 11). They appear in an edge band, dense near the border, with a center clearing wide enough to build several dozen buildings.
- **F-WORLD-03 (MUST):** Town Hall is placed at the grid center (`GRID_SIZE // 2, GRID_SIZE // 2`) on game start.
- **F-WORLD-04 (MUST):** Stone deposits (see `F-STONE`) generate during world initialization in addition to trees.

### F-STONE — Stone Deposits

- **F-STONE-01 (MUST):** A `Stone` is a per-tile world entity carrying `units: int` (default initial value `STONE_UNITS_PER_TILE = 15`). The `units` value is hidden from the UI; players never see a numeric value on the map.
- **F-STONE-02 (MUST):** Stone tiles are **impassable** for pathfinding (same blocker treatment as alive trees and building footprints).
- **F-STONE-03 (MUST):** Stone tiles are **un-buildable**: `BuildingRegistry.can_place` rejects placements whose footprint covers any stone tile. This is *unlike* trees, which auto-clear on placement.
- **F-STONE-04 (MUST):** Trees never spawn on stone tiles (and vice-versa: stone generation skips tiles that already contain alive trees).
- **F-STONE-05 (MUST):** Generation algorithm at world init:
  1. Compute the set of valid stone-center tiles: in-grass, **Chebyshev distance ≥ 12** from any Town Hall footprint tile, not occupied, not on a tree.
  2. Pick **3** centers at random (deterministically from a fixed seed for tests). If fewer valid candidates exist, pick as many as possible.
  3. Around each center, pick a random radius `r ∈ [3, 6]` (Chebyshev). Fill **every** tile in the radius with a stone (units=15) provided the tile is in-grass, not a tree, not a building, not the Town Hall footprint, and not already a stone tile (idempotent merge).
- **F-STONE-06 (MUST):** A stonecutter harvests by:
  1. Walking from the camp to a tile **adjacent** (Chebyshev-1) to the chosen stone tile (the stonecutter cannot stand on the stone itself, since stones block movement).
  2. Mining for `MINE_DURATION_MS` (default `10_000` ms, modulated by gather speed bonuses).
  3. Decrementing the stone's `units` by 1; if `units` reaches 0, the stone is removed and the tile becomes plain walkable grass again.
  4. Returning to the assigned `STONE_MINE` camp with `worker.carrying = "stone"`.
  5. Depositing `+1 stone` into both the building's internal storage AND the global `ResourceManager`.
- **F-STONE-07 (MUST):** Stone reservation works exactly like tree reservation: at most one worker may target a given stone tile at a time. Reservations are released on `release_reservations_for(worker)`, on demolition, on completion, and when the stone disappears.
- **F-STONE-08 (MUST):** `assets/world/stone/default.png` is the placeholder asset (procedurally generated grey isometric pile if missing). Asset metadata supports `scale` and `anchor_norm` like buildings.
- **F-STONE-09 (MUST):** Render order: stones draw with the same painter sort key as trees (anchor-bottom isometric; depth = `gx + gy`).

### F-BLD — Buildings (general)

- **F-BLD-01 (MUST):** Five building types: `TOWN_HALL`, `LUMBER_CAMP`, `STONE_MINE`, `IRON_MINE`, `FARM`.
- **F-BLD-02 (MUST):** Each non–town-hall building occupies a 2×2 tile footprint. Town Hall is 3×3.
- **F-BLD-03 (MUST):** Maximum building level is **10** for non–town-hall, **fixed at 1** for Town Hall (cannot upgrade, cannot demolish, cannot build a second one).
- **F-BLD-04 (MUST):** Build cost (= cost to construct level 1):
  - LUMBER_CAMP, STONE_MINE, IRON_MINE, FARM: `wood=100`.
- **F-BLD-05 (MUST):** Upgrade cost from level *L* → *L+1* (L ≥ 1):
  - `wood = 100 × (L + 1)`
  - `stone = 200 × (L + 1 - 4)` if `L + 1 ≥ 5`, else 0  (so level 5 costs +200 stone, level 6 +400, …, level 10 +1200)
  - `iron  = 300 × (L + 1 - 6)` if `L + 1 ≥ 7`, else 0  (so level 7 costs +300 iron, level 8 +600, …, level 10 +1200)
  - **Decision/Interpretation note (recorded in progress.md):** the user wrote "первый уровень здания (постройка) стоит 100 дерева, каждый следующий требует на 100 дерева больше". We interpret this strictly as: *to reach level L you spend `100 × L` wood*; level 5 additionally adds stone; level 7 additionally adds iron. The `+200 per level` for stone and `+300 per level` for iron mirror the wood pattern.
- **F-BLD-06 (MUST):** Production per cycle for resource-buildings with a worker assigned: `5 × level` of the building's resource.
- **F-BLD-07 (MUST):** Each new building starts with **no worker**.

### F-RENDER — Building Rendering

- **F-RENDER-01 (MUST):** Every building present in `BuildingRegistry.all()` MUST be drawn each frame, including the initial Town Hall and any building placed during play. (Critical regression observed in early build: buildings were stored but never rendered.)
- **F-RENDER-02 (MUST):** `Renderer.draw_buildings(surface, world, registry, camera=None)` iterates the registry, sorts by painter's algorithm key `(grid_y + grid_x, grid_x)` so buildings further from the camera draw first, and blits each via `assets.building_sprite(b.type_tag, b.level)`.
- **F-RENDER-03 (MUST):** A building sprite is anchored so that the bottom-center of the sprite sits at the bottom-center of the building's footprint diamond, then offset by `camera.offset`.
- **F-RENDER-04 (MUST):** `main.py` render pipeline order: clear → `draw_world` → `draw_buildings` → `draw_workers` → placement preview → `TopBar` → `BottomBar` → open modal panel.

```python
class Building:
    type: BuildingType
    level: int                          # 1..10 (TownHall locked at 1)
    grid_pos: tuple[int, int]           # top-left tile
    footprint: tuple[int, int]          # (w, h) in tiles
    worker: Optional["Worker"]          # None when empty
    def income(self) -> dict[str, int]: ...
    def upgrade_cost(self) -> dict[str, int]: ...
    def can_upgrade(self) -> bool: ...
```

### F-PLACE — Placement Rules

- **F-PLACE-01 (MUST):** When the player selects a building from the bottom bar, a translucent contour follows the mouse on the isometric grid.
- **F-PLACE-02 (MUST):** The contour is **green** when placement is valid, **red** when invalid.
- **F-PLACE-03 (MUST):** Placement is **invalid** if any of:
  - Footprint extends outside the playable grass field.
  - Footprint overlaps an existing building's footprint.
  - The closest distance (in tiles, Chebyshev) from any tile of the new footprint to any tile of an existing building's footprint is `< 1`.  
    Interpretation: buildings may not touch edge-to-edge or corner-to-corner; there must be at least one free tile gap.
- **F-PLACE-04 (MUST):** Left-click on a valid spot deducts the build cost (only `wood=100`) and places the building. If the player has insufficient resources, no placement happens and the contour stays red.
- **F-PLACE-05 (MUST):** Right-click or `Esc` cancels placement mode.
- **F-PLACE-06 (MUST):** A second Town Hall can never be placed (the Town Hall option is not in the bottom bar).

### F-UI-TOP — Top Bar

- **F-UI-TOP-01 (MUST):** Fixed top strip (height 48 px). Shows 4 resource entries left-to-right:
  `[icon] amount  (+income/cycle)`
- **F-UI-TOP-02 (MUST):** `amount` updates every frame; `+income` updates whenever buildings/workers change.

```
+--------------------------------------------------------------+
| 🍞 200 (+0)   🪵 200 (+5)   🪨 0 (+0)   ⛓ 0 (+0)            |
+--------------------------------------------------------------+
```

### F-UI-BOT — Bottom Bar (build menu)

- **F-UI-BOT-01 (MUST):** Fixed bottom strip (height 96 px). Shows 4 build buttons (Lumber, Stone, Iron, Farm) with icon + name + cost (`100 wood`).
- **F-UI-BOT-02 (MUST):** Clicking a button enters placement mode for that building.
- **F-UI-BOT-03 (MUST):** A button is greyed out (not clickable) if the player cannot afford 100 wood.

```
+--------------------------------------------------------------+
| [Lumber 100🪵] [Stone 100🪵] [Iron 100🪵] [Farm 100🪵]      |
+--------------------------------------------------------------+
```

### F-UI-PANEL — Building Info Panel (modal)

- **F-UI-PANEL-01 (MUST):** Left-click on an existing building (when not in placement mode) opens a centered modal panel.
- **F-UI-PANEL-02 (MUST):** Panel shows:
  - Building name + current level (`"Lumber Camp — Lv 3"`)
  - One-line description (e.g. `"Lumberjack chops trees for wood."`)
  - For producing buildings: an internal storage line `"Storage: stored / capacity"` (capacity = `3 + 2 × (L − 1)`) — see `F-STORE`.
  - For Phase-11 active-cycle buildings (LUMBER_CAMP, STONE_MINE): the per-trip income line is informational only (`"+1 per delivery"`); legacy passive buildings (FARM, IRON_MINE) keep the `+5×level / 10 s` line.
  - Worker status (`"Worker: assigned"` / `"Worker: empty"` / `"Worker: on the way"`).
  - **Upgrade** button with cost text (`"Upgrade to Lv 4 — 400 wood"`); disabled when level=10 or insufficient resources.
  - **Demolish** button (red).
  - Close [×] in top-right corner.
- **F-UI-PANEL-03 (MUST):** Town Hall panel: same layout but **no Demolish**, **no Upgrade**, plus a "Hire Workers" section with one button per worker type (cost `50 food` each). Hire button is disabled if `food < 50`.
- **F-UI-PANEL-04 (MUST):** Closing the panel (× or Esc) returns to normal view.

```
+----------------------------+
| Lumber Camp — Lv 3   [×]   |
| Lumberjack chops trees.    |
| Income: +15 wood / 10 s    |
| Worker: assigned           |
| [ Upgrade — 400 wood ]     |
| [ Demolish ]               |
+----------------------------+
```

### F-DEMO — Demolish

- **F-DEMO-01 (MUST):** Demolishing removes the building from the registry. No refund.
- **F-DEMO-02 (MUST):** If the demolished building had a worker, that worker becomes **idle** and visually stands at the building's former center tile until reassigned.

### F-UPG — Upgrade

- **F-UPG-01 (MUST):** Upgrade deducts the resources (per F-BLD-05) and increments `level` by 1.
- **F-UPG-02 (MUST):** Income is recalculated immediately; next cycle reflects new level.
- **F-UPG-03 (MUST, **revised**):** For resource-producing buildings, leveling no longer increases passive `5 × level` income. Instead, each level beyond 1 grants the building's *staffed worker* the following permanent additive bonuses:
  - **+5 % movement speed** per level above 1 (effective speed multiplier `1 + 0.05 × (level − 1)`, additive across other bonuses).
  - **+5 % gathering speed** per level above 1 (chop, mine, harvest — applied to the duration of one cycle of work; e.g. level 3 ⇒ 10 % faster ⇒ chop time `CHOP_DURATION_MS / 1.10`).
  - The bonus applies only while the worker is currently assigned to that building. On reassignment / demolition the bonus disappears.
- **F-UPG-04 (MUST):** Town Hall remains non-upgradeable in the original sense (capped at level 1) **only** for the no-demolish/single-building rule; the actual Town Hall progression already implemented (levels 1..10 unlocking tech) stays as is.

### F-CHAR — Worker Characteristics

- **F-CHAR-01 (MUST):** Every worker has a `Characteristics` block with at least:
  - `move_speed_mult: float` — multiplies `1 / WORKER_TILE_TRAVEL_MS` (i.e. effective travel time per tile = `WORKER_TILE_TRAVEL_MS / move_speed_mult`).
  - `gather_speed_mult: float` — multiplies the cycle work rate (effective work duration = `WORK_BASE_MS / gather_speed_mult`).
- **F-CHAR-02 (MUST):** Characteristics start at base `1.0`. Bonuses are accumulated **additively** in fixed-point fashion: a permanent +5 % from a level-2 building stacks with a separate temporary −10 % from some future debuff to give `1.0 + 0.05 − 0.10 = 0.95` (clamped at a positive minimum, e.g. `0.10`).
- **F-CHAR-03 (MUST):** Two bonus categories MUST be supported:
  - **Permanent** — tied to a stable source like the assigned building's level. Applied while the source is valid; removed on demolition/reassignment.
  - **Temporary** — bound to an expiry timestamp; auto-expires at `now_ms ≥ expires_at_ms`.
- **F-CHAR-04 (MUST):** Adding/removing bonuses is observable from tests: `worker.bonuses.add_permanent(source, kind, value)`, `worker.bonuses.add_temporary(kind, value, expires_at_ms)`, `worker.bonuses.remove_source(source)`. The `Characteristics` derived multipliers are recomputed lazily or on-mutation.
- **F-CHAR-05 (MUST):** A LUMBERJACK assigned to a level-`L` Lumber Camp MUST always reflect bonuses `+0.05 × (L − 1)` to both `move_speed_mult` and `gather_speed_mult` from the source `("building_level", camp_id)`. Same rule applies to STONECUTTER, MINER, and FARMER once they have active gathering.

### F-STORE — Production Building Internal Storage

- **F-STORE-01 (MUST):** Every resource-producing building (`LUMBER_CAMP`, `STONE_MINE`, `IRON_MINE`, `FARM`) has an internal storage with a typed slot count and a `stored: int` counter (units currently held).
- **F-STORE-02 (MUST):** Storage capacity scales with level: `capacity(L) = 3 + 2 × (L − 1)` (so 3 at L1, 5 at L2, … 21 at L10).
- **F-STORE-03 (MUST):** A worker assigned to such a building MUST NOT start a new gathering cycle when `stored >= capacity(level)`. The worker waits inside the building until storage drops below capacity.
- **F-STORE-04 (MUST):** Each completed gathering cycle deposits `+1` into the building's internal storage, **and** also adds `+1` to the global `ResourceManager` (this matches the current Lumber Camp behaviour). Future phases will move resources off-site to free up storage; this phase only fills it up.
- **F-STORE-05 (MUST):** The building's panel shows a `Storage: stored / capacity` line. For `LumberCamp` the existing `Wood delivered: N` counter remains as a separate lifetime counter.
- **F-STORE-06 (SHOULD):** The storage lines for FARM / STONE_MINE / IRON_MINE appear in their respective panels (`BuildingPanel`, generic) using `building.stored` and `building.storage_capacity()`.

### F-WORK — Workers

- **F-WORK-01 (MUST):** Four worker types: `LUMBERJACK`, `STONECUTTER`, `MINER`, `FARMER`. Each works only in the matching building type (Lumberjack ↔ Lumber Camp, Farmer ↔ Farm, etc.).
- **F-WORK-02 (MUST):** Hiring is initiated from the Town Hall panel; cost is **50 food**. On success, food is deducted and a new idle worker is spawned at the Town Hall.
- **F-WORK-03 (MUST):** Assignment rule: at every state change (worker hired, building built, building demolished, building reassigned), the WorkerManager runs:
  ```
  for each idle worker W of type T:
      find any building B of matching type with no worker
      if found:  reserve B for W, set W target tile to a valid approach tile near B, W starts moving
      else:      W remains idle, standing near Town Hall
  ```
- **F-WORK-04 (MUST):** Workers move smoothly over time on grid paths (no teleport). Movement speed is exactly **1 tile per 3 seconds** (`WORKER_TILE_TRAVEL_MS = 3000`).
- **F-WORK-05 (MUST):** Workers cannot step onto tiles occupied by any building footprint. Pathfinding treats occupied tiles as blocked.
- **F-WORK-06 (MUST):** For a target production building, a worker may approach from any side. The destination tile is any free grass tile Chebyshev-distance `1` from the building footprint.
- **F-WORK-07 (MUST):** Pathfinding algorithm is **BFS** (not A*), 8-directional (N, S, E, W, and diagonals), uniform step cost 1 per tile.
- **F-WORK-07a (MUST):** Deterministic neighbor order for BFS expansion: `N, NE, E, SE, S, SW, W, NW` (dx/dy: `(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)`).
- **F-WORK-07b (MUST):** No corner-cutting through blocked diagonals: for diagonal step `(x,y)->(x+dx,y+dy)`, at least one of orthogonal side tiles `(x+dx,y)` or `(x,y+dy)` must be walkable.
- **F-WORK-07c (MUST):** If no path exists, worker remains waiting and retries on each assignment recalculation.
- **F-WORK-08 (MUST):** A worker contributes production only when in `working` state (destination reached and building still valid).
- **F-WORK-09 (MUST):** If a building is demolished while a worker is moving to it or working in it, that worker transitions to idle at its current tile and may be reassigned.
- **F-WORK-10 (MUST):** Workers are visualized as small dots moving smoothly between tile centers (interpolated position each frame).
- **F-WORK-11 (MUST):** The Town Hall does not consume a worker slot itself.
- **F-WORK-12 (MUST):** STONECUTTER follows the same active-cycle state machine as LUMBERJACK (Phase 11) but on stone tiles instead of trees. States: `idle → moving (to camp) → working (rest) → going_to_stone → mining → returning → arrived_camp → depositing → working`. The `worker.carrying` flag carries `"stone"` instead of `"wood"` on the way back. Mining duration is `MINE_DURATION_MS` (gather-speed-bonus-aware).
- **F-WORK-13 (SHOULD):** MINER and FARMER currently keep passive `5 × level` production (legacy income), **but** their internal storage gates production: a tick that would deposit when `stored >= capacity` is skipped. They will gain active gather cycles in a future phase (out of scope for Phase 12).

### F-PROD — Production

- **F-PROD-01 (MUST, **revised**):** Production is no longer a flat `5 × level` per tick.
  - For `LUMBER_CAMP` (Phase 11) and `STONE_MINE` (Phase 12): production happens on each completed gather cycle (`+1` resource, modulated by worker gather-speed bonuses), not per tick.
  - For `FARM` and `IRON_MINE` (legacy): keep `5 × level` per tick **only while** internal storage has free space, otherwise no production this tick. (Active-cycle rework planned for a future phase.)
- **F-PROD-02 (MUST):** Production is atomic per-tick (no fractional accumulation between ticks).
- **F-PROD-03 (MUST):** All production also fills the source building's internal storage (F-STORE).

### F-INPUT — Input

- **F-INPUT-01 (MUST):** Mouse: left-click = primary action.
- **F-INPUT-02 (MUST):** Right mouse button is dual-purpose with a 4-pixel drag threshold:
  - **Drag** (RMB held + cursor moves ≥ 4 px from press position): pan the camera (F-CAM-05). While a drag is in progress, the placement preview and any open panel remain on screen and continue to track world coordinates correctly.
  - **Click** (RMB pressed and released with total motion < 4 px): cancel placement mode and/or close the open panel. Same effect as `Esc`.
- **F-INPUT-03 (MUST):** `Esc` cancels placement / closes panel. No other keyboard shortcuts are required.

---

## 4. Non-Functional Requirements

| ID        | Category       | Requirement                                                                                   |
|-----------|----------------|-----------------------------------------------------------------------------------------------|
| NFR-PERF-01 | Performance  | Game must hold ≥ 55 FPS with up to 100 buildings + 100 workers on a 5-year-old laptop iGPU.   |
| NFR-PERF-02 | Performance  | Memory footprint < 250 MB during play.                                                        |
| NFR-REL-01  | Reliability  | No unhandled exceptions during a 10-minute play session reach the user; all logged to stderr. |
| NFR-REL-02  | Cleanup      | On window close, `pygame.quit()` called, no zombie processes, no leaked file handles.         |
| NFR-EXT-01  | Extensibility| Adding a new resource-building type = one subclass + one entry in the bottom-bar config.      |
| NFR-START-01| Startup      | From double-click on `.exe` to interactive game ≤ 3 seconds on warm SSD.                      |
| NFR-FILE-01 | Filesystem   | Game writes no files unless absolutely necessary; if writing, only inside its own folder.     |
| NFR-OS-01   | Portability  | Game `.exe` runs on Windows 11 with no preinstalled software (other than what ships with OS).|

---

## 5. Testing Requirements

### Test infrastructure

- `tests/conftest.py` sets `os.environ["SDL_VIDEODRIVER"] = "dummy"` before importing pygame, allowing UI/asset tests to run headless on CI / in ralph-loop.
- pytest discovers `tests/test_*.py`. Run with `pytest -q`.
- Coverage target: ≥ 85 % on non-UI modules (`config`, `iso`, `resources`, `world`, `buildings/*`, `workers`, `tick`).

### Test → coverage map

| Test file              | Covers                                                                |
|------------------------|-----------------------------------------------------------------------|
| `test_config.py`       | constants present, sane ranges                                        |
| `test_iso.py`          | `world_to_screen`/`screen_to_world` round-trip                        |
| `test_resources.py`    | add/spend/has/initial values                                          |
| `test_world.py`        | grid bounds, grass/tree zones, occupancy                              |
| `test_costs.py`        | upgrade cost formula at L1..L10 (incl. stone@5+, iron@7+)             |
| `test_buildings.py`    | each subclass: type, footprint, income, level cap                     |
| `test_registry.py`     | placement valid/invalid, distance rule, second-town-hall rejected     |
| `test_workers.py`      | hire deducts food, idle queue, type-matched assignment                |
| `test_tick.py`         | 10-second tick boundary, callback called once per cycle               |
| `test_production.py`   | end-to-end: building + worker → resource added per cycle              |

---

## 6. API Specification

This is a single-process desktop app — no HTTP API. Internal module APIs:

### `game.resources`
```python
ResourceManager()
  .get(name) -> int
  .add(name, n) -> None
  .has(cost: Mapping[str,int]) -> bool
  .try_spend(cost: Mapping[str,int]) -> bool
  .per_cycle: dict[str,int]            # property, recomputed by registry/workers
```

### `game.buildings.costs`
```python
build_cost(building_type) -> dict[str,int]            # always {"wood":100}
upgrade_cost(current_level: int) -> dict[str,int]     # for level current+1
```

### `game.buildings.registry`
```python
BuildingRegistry(world)
  .can_place(b_type, grid_pos) -> bool
  .place(b_type, grid_pos) -> Building
  .demolish(building) -> None
  .at(grid_pos) -> Optional[Building]
  .all() -> list[Building]
```

### `game.workers`
```python
WorkerManager(resources, registry)
  .hire(worker_type) -> Optional[Worker]   # None if not enough food
  .reassign_all() -> None                  # called after any placement/demolish/hire/upgrade
  .update(now_ms: int) -> None             # advances movement along current path
  .working_buildings() -> list[Building]   # only buildings whose worker reached destination
  .idle() -> list[Worker]
```

### `game.pathfinding`
```python
find_path_bfs(
  world,
  start: tuple[int, int],
  goal: tuple[int, int],
  blocked: set[tuple[int, int]],
) -> list[tuple[int, int]] | None
# Returns inclusive path [start, ..., goal] or None when unreachable.
# Uses 8-direction BFS, deterministic neighbor order, and no-corner-cutting.
```

### `game.tick`
```python
TickScheduler(period_ms=10_000)
  .update(now_ms) -> bool                  # True iff a tick fired this frame
```

### `game.camera`
```python
Camera(initial_offset=(0,0))
  .offset: tuple[int,int]
  .pan(dx: int, dy: int) -> None
  .clamp(viewport_size: tuple[int,int], world_bounds_px: tuple[int,int,int,int]) -> None
  # world_bounds_px = (min_world_x, min_world_y, max_world_x, max_world_y)
```

### `game.render` (Renderer additions)
```python
Renderer.draw_buildings(surface, world, registry, camera=None) -> None
# All other draw_* methods accept an optional `camera` argument and apply offset.
```

---

## 7. Implementation Tasks

The full ordered task list is the source of truth in `progress.md`. Summary:

| Phase                                  | Tasks    | Status     |
|----------------------------------------|----------|------------|
| 1. Project foundation                  | T01–T07  | done       |
| 2. Resources & top bar                 | T08–T13  | done       |
| 3. World & rendering                   | T14–T17  | done       |
| 4. Buildings & placement               | T18–T25  | done       |
| 5. Building panel & actions            | T26–T30  | done       |
| 6. Workers                             | T31–T36  | done       |
| 7. Production, polish, package         | T37–T42  | done       |
| 8. Render fixes & camera pan           | T43–T51  | done       |
| 9. Worker movement & spacing           | T52–T62  | done       |
| 10. Tree entities & layering           | T63–T74  | done       |
| 11. Lumberjack chop cycle              | T75–T91  | done       |
| 12. Level bonuses, storage, stones     | T92+     | in-progress |

Phases 1–10 are summarised in `progress_archive.md`. Live phases (11+) live in
`progress.md`. See `progress.md` for the canonical task list.

---

## 8. Dependencies

`requirements.txt`:

```
pygame==2.5.2
pytest==8.3.3
pyinstaller==6.10.0
ruff==0.6.9
```

No other runtime dependencies. PyInstaller bundles pygame + Python interpreter
into the final `.exe`, so the end user needs nothing preinstalled.

---

## 9. Out of Scope

- Save / load, main menu, options screen, audio, music, sound effects.
- Combat, enemies, fog of war, day/night cycle.
- Multiplayer, networking.
- Localization (English only in UI).
- Mod support.
- Camera zoom / rotation (panning is supported via RMB drag).
- Mac / Linux builds.

### Out of scope for Phase 12 specifically

- Active gather cycles for FARMER and MINER (they remain passive within a storage-capped tick; activation cycles will be added in a later phase together with farm fields and iron veins).
- Off-site resource transport from production buildings (storage just fills up; pickup carts come later).
- Stone respawn / regrowth — when a stone tile is depleted, it stays plain grass.

---

## 10. Glossary

| Term            | Meaning                                                               |
|-----------------|------------------------------------------------------------------------|
| Cycle / Tick    | A 10-second game-clock interval that triggers production.            |
| Footprint       | The set of tiles a building occupies on the grid.                    |
| Grass field     | The 32×32 playable interior; only place buildings can be placed.     |
| Idle worker     | A hired worker without a building assigned; stands near Town Hall or on its former tile after demolition. |
| Income          | Resources added to the player per single cycle.                       |
| Town Hall       | The single mandatory starting building; can hire workers; cannot be upgraded, demolished, or duplicated. |
