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
| Assets                   | Disk-first PNG + procedural fallback | Small placeholders in-repo; swap without code changes |

### Project directory tree

```
game/
├── PRD.md                       # product contract (update only via explicit progress tasks)
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
│       │   └── registry.py      # BuildingRegistry, placement validation
│       ├── workers.py           # Worker, WorkerManager, assignment
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── top_bar.py       # population / housing HUD
│       │   ├── bottom_bar.py    # building selection menu
│       │   ├── placement.py     # mouse-follow contour, click to place
│       │   ├── building_panel.py# modal: info / demolish / upgrade
│       │   └── town_hall_panel.py # Town Hall-specific panel actions
│       ├── render.py            # main scene renderer
│       └── input.py             # mouse/keyboard event router
└── tests/
    ├── __init__.py
    ├── conftest.py              # SDL_VIDEODRIVER=dummy, fixtures
    ├── test_config.py
    ├── test_iso.py
    ├── test_resources.py
    ├── test_world.py
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
- **F-RES-03 (MUST):** ResourceManager exposes `get(name)`, `add(name, n)`.
- **F-RES-04 (MUST):** Per-cycle income (computed from active buildings + workers) is exposed for UI as a dict.

```python
class ResourceManager:
    def get(self, name: str) -> int: ...
    def add(self, name: str, amount: int) -> None: ...
    @property
    def per_cycle(self) -> dict[str, int]: ...
```

### F-TICK — Cycle System

- **F-TICK-01 (MUST):** A cycle lasts exactly **10 seconds** of wall-clock game time (using `pygame.time.get_ticks()`).
- **F-TICK-02 (MUST, revised):** Cycle ticks drive tick-based systems only (e.g., legacy passive producers). Active gather buildings produce via worker state machines (see **F-PROD-01**).

### F-ISO — Isometric Projection

- **F-ISO-01 (MUST):** Tile size 64×32 (classic 2:1 diamond). No zoom, no rotation. Camera **pan via RMB drag** is supported (see F-CAM).
- **F-ISO-02 (MUST):** `iso.world_to_screen(gx, gy)` and `iso.screen_to_world(px, py)` are inverses (rounded to int grid). They operate in *world* pixels; camera offset is applied separately by the renderer.

### F-CAM — Camera Pan

- **F-CAM-01 (MUST):** A `Camera` carries an integer `offset = (ox, oy)` in pixels, initially `(0, 0)`.
- **F-CAM-02 (MUST):** `Renderer.draw_world`, `draw_buildings`, `draw_workers` and the placement preview apply `camera.offset` before blitting. `TopBar`, `BottomBar` and modal panels are drawn in **screen** coordinates and DO NOT pan.
- **F-CAM-03 (MUST):** `screen_to_grid` subtracts `camera.offset` before calling `iso.screen_to_world`, so clicks land on the correct world tile when panned.
- **F-CAM-04 (MUST):** `camera.clamp(viewport_size, world_bounds_px)` keeps the world's bounding box (grass + tree skirt) inside the viewport play area (between TopBar and BottomBar). When the world is bigger than the viewport, only previously off-screen parts can be revealed; when smaller, the offset is locked at the centering value.
- **F-CAM-05 (MUST):** Camera UX = **"grab-and-drag the world"**: if the mouse moves by `(dx, dy)` while RMB is held, then `camera.offset += (dx, dy)` (the world moves with the cursor), then immediately clamped per F-CAM-04.

### F-PATH — Pathfinding & Movement Rules

- **F-PATH-01 (MUST):** Workers move only along the four cardinal directions
  (N, E, S, W). Diagonal movement is forbidden. Every consecutive pair of
  tiles in any worker path satisfies `abs(dx) + abs(dy) == 1`. Implemented in
  `src/game/pathfinding.py` as a 4-direction BFS; resource-search BFS in
  `src/game/world.py` (`find_nearest_free_tree`, `find_nearest_free_stone`)
  uses the same neighbour set.
- **F-PATH-02 (MUST):** A path is `None` (unreachable) iff there is no
  4-connected sequence of walkable tiles from start to goal. There is no
  diagonal corner-cutting fallback.
- **F-PATH-03 (MUST):** `find_path_bfs` is deterministic for fixed inputs:
  the same `(start, goal, blocked)` returns the exact same list of tiles.
- **F-PATH-04 (MUST):** Worker dispatch (`reassign_all`,
  `_start_gather_cycle`, `_start_return_to_camp`) must build the `blocked`
  set via `World.blocked_tiles()` (cached union, see API spec). It must NOT
  iterate `range(world.height) × range(world.width)`.

### F-WORLD — World

- **F-WORLD-01 (MUST):** A `GRID_SIZE × GRID_SIZE` tile playable grass field (currently 110×110 in `game_settings.json`), centered on screen. Camera pan is required to see the whole map.
- **F-WORLD-02 (MUST, **revised**):** Trees are world-owned entities (Phase 10) that block movement and can be chopped (Phase 11). **Generation — grove centers (10 total):** **First**, try to pick **two** priority centers (PRNG order within each ring): one whose minimum Chebyshev distance to any Town Hall footprint tile is **exactly 12**, one whose minimum is **exactly 20**. Each must lie on grass, not on a stone tile, and the Chebyshev disk of radius **8** (max grove radius) around the center must contain **no** stone tiles. The two centers must be at least **17** tiles apart (Chebyshev) so max-radius groves cannot overlap. If no such pair exists, skip priority groves. **Then** pick **8** additional grove centers the same way as stone-cluster centers (in-grass, outside the central build clearing, **Chebyshev distance ≥ 12** from every Town Hall footprint tile, centers not on stone), excluding already-chosen center tiles. **Filling groves:** around each center choose random `r ∈ [5, 8]` (Chebyshev). For each tile in that disk: skip if not in-grass, on stone, or already a tree; skip the Town Hall footprint; skip tiles inside the central build-clearing zone **unless** the grove is one of the two priority groves (those may place under the clearing rule so groves near the TH actually appear). Otherwise place a tree with **70%** independent probability (PRNG). **Scatter pass:** then place up to **`floor(GRID_SIZE² × 0.02)`** additional trees on a shuffled list of all remaining eligible grass tiles (same clearing / stone / no-overlap rules as non-priority groves; PRNG). Default `World()` seeds stone and tree RNG from OS entropy so layouts differ between games; optional `World(world_seed=int)` reproduces a layout for tests. Stages use `stage_from_tile_seed` per placed tile.
- **F-WORLD-03 (MUST):** Town Hall is placed on game start as a 3×3 footprint centred on the map: top-left tile `(GRID_SIZE // 2 - 1, GRID_SIZE // 2 - 1)` (see `town_hall_origin_tile()` in `config.py` / `main.py`).
- **F-WORLD-04 (MUST):** Stone deposits (see `F-STONE`) generate during world initialization in addition to trees.

### F-STONE — Stone Deposits

- **F-STONE-01 (MUST):** A `Stone` is a per-tile world entity carrying `units: int` (default initial value `STONE_UNITS_PER_TILE = 15`). The `units` value is hidden from the UI; players never see a numeric value on the map.
- **F-STONE-02 (MUST):** Stone tiles are **impassable** for pathfinding (same blocker treatment as alive trees and building footprints).
- **F-STONE-03 (MUST):** Stone tiles are **un-buildable**: `BuildingRegistry.can_place` rejects placements whose footprint covers any stone tile. This is *unlike* trees, which auto-clear on placement.
- **F-STONE-04 (MUST):** Trees never spawn on stone tiles (and vice-versa: stone generation skips tiles that already contain alive trees).
- **F-STONE-05 (MUST):** Generation algorithm at world init:
  1. Compute the set of valid stone-center tiles: in-grass, **Chebyshev distance ≥ 12** from any Town Hall footprint tile, not occupied, not on a tree.
  2. Pick **6** centers at random (PRNG). **One** mandatory center lies on the Chebyshev ring at distance **20** from Town Hall (with generation rules that do not silently drop that cluster); others follow spacing rules documented in code (`world.py`). If fewer valid candidates exist, pick as many as possible.
  3. Around each center, pick a random radius `r ∈ [1, 4]` (Chebyshev). Fill **every** tile in the radius with a stone (units=15) provided the tile is in-grass, not a tree, not a building, not the Town Hall footprint, and not already a stone tile (idempotent merge).
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

- **F-BLD-01 (MUST):** Implemented building types include at least: `TOWN_HALL`, `LUMBER_CAMP`, `STONE_MINE`, `IRON_MINE`, `FARM`, `FORESTER_HUT`, `SCHOOL`, **`HOUSE`** (social). The bottom bar uses multi-level menus (Resource / Social / Processing / Dev); exact membership may grow—each type is registered in config + placement map.
- **F-BLD-02 (MUST):** Standard production/social buildings (incl. `HOUSE`, `SCHOOL`) use a **2×2** footprint unless noted. Town Hall is **3×3**.
- **F-BLD-03 (MUST):** Maximum level is **10** for upgradable producer/social buildings. **Town Hall** is unique (exactly one), cannot be demolished, cannot be built from the menu, **can upgrade** levels 1..10 for tech gates. **`FORESTER_HUT`** is capped at level 1 where implemented.
- **F-BLD-04 (MUST):** Building placement is **free** (no wallet spend gate).
- **F-BLD-05 (MUST):** Upgrades are **free** (no wallet spend gate).
- **F-BLD-06 (MUST, revised):** Production model is defined by **F-PROD**: mixed tick-based and active-cycle production depending on building type.
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
- **F-PLACE-04 (MUST):** Left-click on a valid spot places the building (no cost deduction gate).
- **F-PLACE-05 (MUST):** Right-click or `Esc` cancels placement mode.
- **F-PLACE-06 (MUST):** A second Town Hall can never be placed (the Town Hall option is not in the bottom bar).

### F-UI-TOP — Top Bar

- **F-UI-TOP-01 (Phase 15, MUST):** Fixed top strip (height 48 px). **Does not** display the four resource rows or per-cycle income (those lines are removed from the HUD in this phase).
- **F-UI-TOP-02 (Phase 15, MUST):** Shows **population / housing**: a **population icon** (disk asset under `assets/` with procedural fallback — see **F-POP-UI**) followed by text:
  `current (max max_cap)` — e.g. **`3 (max 8)`** where `current` is the living population count and `max_cap` is total housing capacity (see **F-HOUSING**).
- **F-UI-TOP-03 (SHOULD):** Icon and numbers align vertically centered in the strip; readable at 1280×720.

```
+--------------------------------------------------------------+
| [pop icon]  3 (max 8)                                         |
+--------------------------------------------------------------+
```

### F-UI-BOT — Bottom Bar (build menu)

- **F-UI-BOT-01 (MUST):** Fixed bottom strip (**96 px**). Uses a **multi-level** menu: categories (**Main → Resource / Social / Processing / Dev**) with a **Back** control to Main. Production buildings live under Resource; **School** and **House** under Social; Processing may be empty; Dev holds debug place-tree / place-stone tools where implemented.
- **F-UI-BOT-02 (MUST):** Selecting a leaf building posts a placement intent with that building type.
- **F-UI-BOT-03 (MUST):** Buttons are gated by tech/state rules (Town Hall level, mode), not by wallet affordability.

### F-UI-PANEL — Building Info Panel (modal)

- **F-UI-PANEL-01 (MUST):** Left-click on an existing building (when not in placement mode) opens a centered modal panel.
- **F-UI-PANEL-02 (MUST):** Panel shows:
  - Building name + current level (`"Lumber Camp — Lv 3"`)
  - One-line description (e.g. `"Lumberjack chops trees for wood."`)
  - For producing buildings: an internal storage line `"Storage: stored / capacity"` (capacity = `3 + 2 × (L − 1)`) — see `F-STORE`.
  - For Phase-11 active-cycle buildings (LUMBER_CAMP, STONE_MINE): the per-trip income line is informational only (`"+1 per delivery"`); legacy passive buildings (FARM, IRON_MINE) keep the `+5×level / 10 s` line.
  - Worker status (`"Worker: assigned"` / `"Worker: empty"` / `"Worker: on the way"`).
  - **Upgrade** button with free-action text (`"Upgrade to Lv 4 — Free"`); disabled when level=10 or blocked by explicit state/tech gate.
  - **Demolish** button (red).
  - Close [×] in top-right corner.
- **F-UI-PANEL-03 (MUST):** Town Hall panel: **no Demolish**, **Upgrade** when TH leveling is unlocked; **no hiring** — all hiring/training happens at **School** (see **F-SCHOOL-Q**).
- **F-UI-PANEL-04 (MUST):** Closing the panel (× or Esc) returns to normal view.

```text
Panel example is illustrative only; exact lines depend on building type
(active-cycle buildings show status/storage rather than legacy passive income).
```

### F-DEMO — Demolish

- **F-DEMO-01 (MUST):** Demolishing removes the building from the registry. No refund.
- **F-DEMO-02 (MUST):** If the demolished building had a worker, that worker becomes **idle** and visually stands at the building's former center tile until reassigned.

### F-UPG — Upgrade

- **F-UPG-01 (MUST):** Upgrade increments `level` by 1 (free action).
- **F-UPG-02 (MUST):** Income is recalculated immediately; next cycle reflects new level.
- **F-UPG-03 (MUST, **revised**):** For resource-producing buildings, leveling no longer increases passive `5 × level` income. Instead, each level beyond 1 grants the building's *staffed worker* the following permanent additive bonuses:
  - **+5 % movement speed** per level above 1 (effective speed multiplier `1 + 0.05 × (level − 1)`, additive across other bonuses).
  - **+5 % gathering speed** per level above 1 (chop, mine, harvest — applied to the duration of one cycle of work; e.g. level 3 ⇒ 10 % faster ⇒ chop time `CHOP_DURATION_MS / 1.10`).
  - The bonus applies only while the worker is currently assigned to that building. On reassignment / demolition the bonus disappears.
- **F-UPG-04 (MUST):** Town Hall is **unique** (single instance, no demolish) **and** may **upgrade** levels 1..10 for tech and housing unlocks; only the no-second-TH rule is absolute.

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

### F-HOUSING — Housing Capacity

- **F-HOUSING-01 (Phase 15, MUST):** Each **hired / living** worker occupies **one** housing slot. `current_population =` number of workers currently in the world.
- **F-HOUSING-02 (Phase 15, MUST):** **Town Hall** at level `L` (1..10) contributes **`housing_th(L) = 8 + 2 × (L − 1)`** slots.
- **F-HOUSING-03 (Phase 15, MUST):** **`HOUSE`** (see **F-HOUSE**) at level `L` contributes **`housing_house(L) = 2 + 2 × (L − 1)`** slots.
- **F-HOUSING-04 (Phase 15, MUST):** **`max_population` =** sum of housing from the one Town Hall plus every **placed** `HOUSE` (by building level). Other building types contribute **0** unless specified in a future amendment.
- **F-HOUSING-05 (Phase 15, MUST):** A new training request or instant hire that would make `current_population > max_population` **must be rejected** (UI disabled or no-op with clear affordance in Phase 15 minimum: disabled control).

### F-POP-UI — Population HUD Asset

- **F-POP-UI-01 (Phase 15, MUST):** A small **population** icon is loaded **disk-first** from `assets/ui/population/` (exact filename convention matches existing asset loader patterns, e.g. `default.png` + optional `asset_meta.json`).
- **F-POP-UI-02 (Phase 15, MUST):** If the file is missing, `assets.py` provides a **procedural** silhouette so the HUD never crashes in headless tests.

### F-SCHOOL-Q — School Training Queue

- **F-SCHOOL-Q-01 (Phase 15, MUST):** Each **`SCHOOL`** exposes a **FIFO training queue** of up to **7** pending trainees.
- **F-SCHOOL-Q-02 (Phase 15, MUST):** Ordering a worker type **enqueues** into the **leftmost empty** slot (visual **left → right** row of **7** squares). Training is **free**; housing cap is the gating mechanic.
- **F-SCHOOL-Q-03 (Phase 15, MUST):** Only the **front** item (leftmost occupied slot) progresses. Training one unit takes **30_000 ms** wall-clock game time (`now_ms` delta), shown as a **yellow** progress bar along the **bottom** inside that square, with the **worker-type icon** filling the cell above.
- **F-SCHOOL-Q-04 (Phase 15, MUST):** When training completes, the worker **spawns** at that school using the same spawn rules as the current **School hire** implementation (bottom-edge approach / fallbacks). The completed icon is removed; entries **shift left** compacting the queue; if other entries remain, the new front entry **starts** training from **0** progress.
- **F-SCHOOL-Q-05 (Phase 15, MUST):** Multiple schools each maintain an **independent** queue and independent timers.

### F-HOUSE — House (social)

- **F-HOUSE-01 (Phase 15, MUST):** Building type **`HOUSE`**, **2×2** footprint, levels **1..10**, placed from the **Social** submenu.
- **F-HOUSE-02 (Phase 15, MUST):** House upgrades follow global free-upgrade rules from **F-BLD-05**.
- **F-HOUSE-03 (Phase 15, MUST):** Demolishing a house reduces `max_population`; if `current_population > max_population` after demolition, behaviour for **Phase 15** is implementation-defined but **must** be asserted in tests (recommended: block demolition while over-cap, or forbid demolish when it would violate cap—pick one in TDD).

### F-WORK — Workers

- **F-WORK-01 (MUST):** Worker types include at least `LUMBERJACK`, `STONECUTTER`, `MINER`, `FARMER`, `FORESTER`. Each production type works only in its matching building (`FORESTER` ↔ `FORESTER_HUT`, etc.).
- **F-WORK-02 (Phase 15, MUST):** **Acquiring** workers is done only through **School** training queue (**F-SCHOOL-Q**), not the Town Hall panel. Worker acquisition is free. Spawning still respects **F-HOUSING**.
- **F-WORK-03 (MUST):** Assignment rule: at every state change (worker finished training, building built, demolished, upgrade, etc.), WorkerManager runs `reassign_all` (see implementation) to match idle workers to unstaffed compatible buildings.
- **F-WORK-04 (MUST):** Workers move smoothly on grid paths (**F-PATH**). Base travel time **WORKER_TILE_TRAVEL_MS** is modulated by characteristics.
- **F-WORK-05 (MUST):** Workers cannot step onto building footprint tiles; pathfinding uses **`World.blocked_tiles()`** and **4-direction BFS** (**F-PATH** obsolete / superseded: ~~8-direction worker movement~~ removed).
- **F-WORK-06 (MUST):** For a target production building, approach tiles are orthogonally adjacent (Chebyshev-1) walkable grass tiles outside the footprint (see implementation).
- **F-WORK-07 (MUST):** Pathfinding for workers is **exactly** `find_path_bfs` with **four** neighbours **N, E, S, W** — see **F-PATH-01**. (Earlier PRD drafts describing 8-neighbour BFS are void.)
- **F-WORK-08 (MUST):** A worker contributes production only when its state machine allows (active gather buildings).
- **F-WORK-09 (MUST):** If a building is demolished while a worker is assigned, that worker becomes idle at current tile (`notify_demolished` semantics).
- **F-WORK-10 (MUST):** Workers are rendered via sprites / interpolation (**F-RENDER** extensions).
- **F-WORK-11 (MUST):** Town Hall does not occupy a worker slot.
- **F-WORK-12 (MUST):** STONECUTTER mirrors LUMBERJACK cycle on stones (Phase 12); FORESTER follows planting cycle (Phase 14).
- **F-WORK-13 (SHOULD):** MINER/FARM passive tick behaviour remains storage-gated until a future activation phase.

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
| NFR-PERF-03 | Performance  | Renderer iterates only the camera-visible tile range each frame; frame cost is independent of map size. |
| NFR-PERF-04 | Performance  | Worker dispatch (assignment, gather scheduling, return paths) runs in O(buildings + entities), not O(W·H), per frame. |
| NFR-REL-01  | Reliability  | No unhandled exceptions during a 10-minute play session reach the user; all logged to stderr. |
| NFR-REL-02  | Cleanup      | On window close, `pygame.quit()` called, no zombie processes, no leaked file handles.         |
| NFR-EXT-01  | Extensibility| Adding a new building type requires subclass + config registration + menu wiring in the multi-level bottom bar. |
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
| `test_resources.py`    | add/get/normalize-name/initial values                                 |
| `test_world.py`        | grid bounds, grass/tree zones, occupancy                              |
| `test_buildings.py`    | each subclass: type, footprint, income, level cap                     |
| `test_registry.py`     | placement valid/invalid, distance rule, second-town-hall rejected     |
| `test_workers.py`      | assignment/state transitions, staffing rules, queue/spawn interactions |
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
  .per_cycle: dict[str,int]            # property, recomputed by registry/workers
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
  .hire(worker_type, *, source_building=None) -> Optional[Worker]
  # direct spawn helper; worker acquisition policy is School queue-driven in Phase 15.
  .reassign_all() -> None                  # called after placement/demolish/training-complete/upgrade
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
# Uses 4-direction BFS (N, E, S, W) with deterministic neighbor order.
# Workers cannot move diagonally; every consecutive step satisfies
# `abs(dx) + abs(dy) == 1`. See F-PATH-01.
```

### `game.world` (cached blocking sets, Phase 13)
```python
World(*, world_seed: int | None = None)  # None: OS-entropy RNG for stones/trees; int: reproducible tests
World.occupied_tiles() -> set[tuple[int, int]]   # building footprints
World.tree_tiles()     -> set[tuple[int, int]]   # alive tree tiles
World.stone_tiles()    -> set[tuple[int, int]]   # alive stone tiles
World.blocked_tiles()  -> set[tuple[int, int]]   # union of the three
# All four return fresh shallow copies; mutating the return value never
# affects the world. Maintained in O(1) by `mark_occupied`, `free`,
# `remove_tree`, `harvest_stone`, and the `_init_*` generators.
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

Renderer.visible_tile_range(surface, world, camera) -> tuple[int, int, int, int]
# (gx_min, gy_min, gx_max_inclusive, gy_max_inclusive), clipped to grid,
# widened by VISIBLE_TILE_MARGIN = 2. Returns an empty range
# (gx_max < gx_min) when nothing on the world is visible. See NFR-PERF-03.
```

---

## 7. Implementation Tasks

The full ordered task list is the source of truth in `progress.md`. Summary:

| Phase                                      | Tasks        | Status   |
|--------------------------------------------|--------------|----------|
| 1–12 (foundation through stone/bonuses)  | T01–T125     | done     |
| 13. Performance & 4-dir pathfinding      | T126–T148    | done     |
| 14. Forestry (Forester, species, trees)    | T149–T160    | done     |
| **15. Housing, House, School queue, HUD**  | **T161–T173** | queued  |

Historical per-phase numbering is archived in **`progress_archive.md`**. **`progress.md`** holds the runnable checklist for Ralph.

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

### Out of scope (current)

- Off-site resource transport from production buildings (storage fills locally for now).
- Stone respawn / regrowth — depleted stone tiles remain plain grass.
- Audio/combat/network/save systems remain out of scope (see section above).

---

## 10. Glossary

| Term            | Meaning                                                               |
|-----------------|------------------------------------------------------------------------|
| Cycle / Tick    | A 10-second game-clock interval that triggers production.            |
| Footprint       | The set of tiles a building occupies on the grid.                    |
| Grass field     | The `GRID_SIZE × GRID_SIZE` playable interior (`game_settings.json`); only place buildings can be placed. |
| Idle worker     | A worker without a building assignment; stands at current/stand tile until reassigned. |
| Income          | Resources added to the player per single cycle.                       |
| Town Hall       | The single mandatory starting building; upgrades for tech/housing; **cannot** be demolished or duplicated; hiring is delegated to **School** (Phase 15). |
| House           | Social building (+housing capacity); see **F-HOUSE**. |
| Population      | `current` worker count vs `max` housing (see **F-HOUSING**). |
