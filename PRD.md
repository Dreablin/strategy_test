# PRD — Isometric Economy Strategy Game

## 1. Agent Context Contract

This PRD is working context for coding agents, not a marketing spec. Prefer
preserving these invariants over literal old phase wording:

- When adding new worker types or worker-operated buildings, follow
  `worker_extension_guide.md` so `src/game/workers.py` stays a coordinator and
  behavior lives in focused worker modules.
- When adding new buildings, follow `building_extension_guide.md` so building
  class state, construction settings, assets, UI, transport, and worker runtime
  stay in their focused modules.
- Per-building balance belongs in `src/game/settings/buildings/<building>.json`.
  Keep construction requirements, local storage capacities, production/work
  action/rest timings, dining eat duration, work/search radii, school training
  settings, and housing capacity there instead of duplicating those values in
  Python code or `game_settings.json`.
- Global game-wide settings belong in `game_settings.json`. Examples:
  window/tile/world sizes, initial Town Hall warehouse, global worker satiety
  max/drain/hunger threshold, worker tier metadata, and Town Hall level gates
  for buildings/hiring. Do not move building-specific balance into
  `game_settings.json`.
- Resources move physically through internal building storages, Town Hall
  warehouse, and carrier transport tasks. Do not reintroduce passive wallet
  production.
- School is the player-facing hiring/training surface. Town Hall does not hire.
- Construction and upgrades are ordered without direct wallet spend, but most
  buildings require resource delivery and build time through `ConstructionSite`.
- Special-case buildings (`FIELD`, `VINEYARD`, `TOWN_HALL`) have intentionally
  different placement, storage, worker, and upgrade rules. `WELL` is a normal
  staffed producer in shape, levels, worker assignment, and local storage; its
  special rule is that `water` is never warehoused at Town Hall.
- When adding a new consumer of an existing resource, prefer capability
  contracts such as `add_wheat_in`, `input_amount`, `input_capacity`,
  `add_water_in`, `water_amount`, `water_capacity` over hard-coded
  `resource -> building type` mappings.

---

## 2. Project Basics

- Runtime: Python 3.10+ with pygame 2.5.2.
- Tests: pytest 8.x; `tests/conftest.py` sets dummy SDL video for headless UI/asset tests.
- Lint: ruff.
- Assets: disk-first PNGs with procedural fallbacks. Missing asset files must not crash tests.
- Source lives in `src/game/`; tests live in `tests/`.
- Game starts immediately in a pygame window; no save/load, title/main menu, audio, networking, combat, fog of war, zoom, or rotation.

---

### F-WIN — Window & Lifecycle

- On launch, open one window titled `"Isometric Strategy"` at 1280×720 or larger within monitor bounds. Loop targets 60 FPS.
- On quit, call `pygame.quit()` and exit cleanly with no background work left running.

### F-RES — Resources

- **F-RES-01 (MUST):** Current resource keys include raw goods, processed goods, food goods, water, and local-only dining meals. All quantities are non-negative integers.
- **F-RES-02 (MUST):** Town Hall warehouse persists only warehouse-scoped resources. It does not store `water`, `simple_meal`, `elite_meal`, or other local-only resources. Starting warehouse contents are configured only in `game_settings.json` / `config.TOWN_HALL_STARTING_WAREHOUSE`.
- **F-RES-03 (MUST):** Resource flow is physical: producers fill building internal storages, processors consume local inputs and fill local outputs, and carriers move units between buildings. Do not add passive per-cycle wallet income.
- **F-RES-04 (MUST):** `water` is not stored in Town Hall. A `WELL` is a staffed producer with **local water storage** (capacity by level in `well.json`). An assigned `WATERMAN` produces `+1` water into that storage when the well is active, completed, and has free space, using the building’s configured work/rest cadence. Carriers execute normal `TransportTask("water", well, consumer, …)` pickups: they take units from the well’s local storage (`take_from_storage` / equivalent) with standard carrier interact timing and deliver to any active **water consumer** that exposes `water_amount`, `water_capacity`, and `add_water_in`. There is **no** well `busy` flag, **no** carrier-side water draw timer, and **no** `WELL_DRAW_WATER_MS` special case.
- **F-RES-05 (MUST):** `simple_meal` is local to `CANTEEN`. It is produced, reserved, and consumed inside canteens; it must not be exported to Town Hall or treated as a generic carrier-delivered warehouse resource.
- **F-RES-06 (MUST):** `elite_meal` is local to `RESTAURANT` with the same locality rule as `simple_meal`: produced, reserved, and consumed inside restaurants only; never exported to Town Hall.

### F-TICK — Cycle System

- Timed systems use `pygame.time.get_ticks()` / `now_ms` deltas. Production is worker-state driven, not passive building ticks.

### F-ISO — Isometric Projection

- Tile size is 64×32. No zoom/rotation. `iso.world_to_screen` and `iso.screen_to_world` operate in world pixels; camera offset is applied separately.

### F-CAM — Camera Pan

- RMB drag pans the world by adding mouse delta to `camera.offset`, then clamps to world bounds.
- Renderer/world/worker/placement views apply camera offset. HUD, bottom bar, and modal panels stay in screen coordinates.
- `screen_to_grid` must subtract camera offset before converting to grid.

### F-PATH — Pathfinding & Movement Rules

- Workers use deterministic 4-direction BFS only: N/E/S/W, no diagonals, no corner-cutting. Every path step satisfies `abs(dx) + abs(dy) == 1`.
- Worker dispatch and resource search must use cached world blocking sets (`World.blocked_tiles()`), not full-grid scans per frame.
- Building footprints, alive trees, stone, blocking iron, and blocking gold are blockers unless a building has explicit special rules.

### F-WORLD — World

- Playable map is `GRID_SIZE × GRID_SIZE` grass from `game_settings.json`. Town Hall starts centered as a 3×3 footprint at `town_hall_origin_tile()`.
- `World(world_seed=int)` must be deterministic for tests. Default `World()` may use entropy for varied layouts.
- Generation order: metal deposits first, then stone, then trees. Later generators must not place over earlier metal/stone resources.
- Trees are world-owned blockers, can be chopped, and use staged disk-first assets/procedural fallback. Placement may auto-clear trees.

### F-STONE — Stone Deposits

- Stone is a per-tile world entity with hidden `units` (default `STONE_UNITS_PER_TILE = 15`).
- Stone tiles are impassable and unbuildable. Trees must not spawn on stone; stone must not spawn on existing trees/metals/buildings.
- Stone generation creates clusters outside the Town Hall area, with one useful cluster near the Town Hall ring. Keep exact generation tuning in the world generation code/settings and tests, not in this PRD.
- Stonecutter stands adjacent to stone, mines using `STONE_MINE` configured work timing, decrements units, removes depleted stone, returns to `STONE_MINE`, deposits into local storage, then carriers export it.
- Stone reservations mirror tree reservations: one worker per resource tile; release on worker cleanup, demolition, completion, or resource disappearance.

### F-METAL — Iron and Gold Deposits

- **F-METAL-01 (MUST):** Metal deposit generation runs before stone and trees. Stone and trees must not spawn on any iron/gold tile.
- **F-METAL-02 (MUST):** Iron deposits include impassable blocking iron core tiles and passable/buildable iron tiles directly adjacent to the core. `IRON_MINE` placement requires overlap with buildable iron and must not overlap blocking iron.
- **F-METAL-03 (MUST):** Iron blocking/gold blocking cluster radius currently uses the reduced range `1..2` (Chebyshev), not the older `3..5` range.
- **F-METAL-04 (MUST):** Gold follows the same map/deposit asset pattern as iron for now, but gold mining, gold workers, and gold resource logistics are not implemented yet.
- **F-METAL-05 (MUST):** Dev placement tools include tree, stone, and iron. Gold dev placement is not implemented unless explicitly added. Add new dev tools explicitly; do not overload existing build menu events silently.

### F-BLD — Buildings (general)

- **F-BLD-01 (MUST):** Current building types include `TOWN_HALL`, `LUMBER_CAMP`, `STONE_MINE`, `IRON_MINE`, `FARM`, `FIELD`, `FORESTER_HUT`, `SAWMILL`, `MILL`, `BAKERY`, `CANTEEN`, `RESTAURANT`, `WELL`, `SCHOOL`, `HOUSE`, `CHICKEN_FARM`, `COW_FARM`, `VINEYARD_FARM`, `VINEYARD`, and `WINERY`. Each type must be registered consistently in building class, config/settings, placement map, assets folder mapping, panels where needed, and bottom-bar menu.
- **F-BLD-02 (MUST):** Standard buildings use a **2×2** footprint unless noted. Exceptions include `TOWN_HALL` as **3×3** and crop/plot tiles such as `FIELD` and `VINEYARD` as **1×1**. If a building has a non-standard footprint, define it through the building class/settings pattern and keep placement, rendering, and tests aligned.
- **F-BLD-03 (MUST):** Most buildings can reach level **10** when construction requirements exist. Exceptions: `FIELD` and `VINEYARD` are crop/plot-state driven and not upgraded; `TOWN_HALL` is unique, cannot be demolished or built from the menu, and can upgrade levels 1..10. `WELL` follows the same level **1..10** construction/upgrade pattern as other upgradable resource buildings when configured in `well.json`.
- **F-BLD-04 (MUST):** Placement order creates a construction site, not an instant finished building, for configured buildings. There is no wallet-spend gate at click time, but construction/upgrades require resource delivery and build time through `ConstructionSite`.
- **F-BLD-05 (MUST):** Each new completed work building starts with **no assigned worker**. `WorkerManager.reassign_all()` may assign an idle compatible worker after construction completes.
- **F-BLD-06 (MUST):** Production model is defined by **F-PROD** (worker-cycle driven, storage-constrained). Do not use `Building.income()` for active resources.

### F-RENDER — Building Rendering

- Draw every registry building every frame. Sort by painter key `(grid_y + grid_x, grid_x)`.
- Building sprites are disk-first via `assets.building_sprite(type_tag, level)` and anchored bottom-center to the footprint diamond.
- Render pipeline: world → buildings → workers → placement preview → TopBar → BottomBar → modal panel.
- `Building` core contract: `type_tag`, `level`, `grid_pos`, class `footprint`, `construction_site`, `is_under_construction`, `max_level()`.

### F-PLACE — Placement Rules

- Selecting a bottom-bar building shows a translucent grid contour: green when valid, red when invalid.
- Invalid placement: outside grass, footprint overlap, regular-building Chebyshev gap `< 2`, unbuildable stone/blocking metal, or invalid `IRON_MINE` overlap.
- `FIELD` is a walkable crop tile, not a regular blocking building for spacing. Fields and buildings may touch, but never overlap.
- Trees are auto-cleared by placement; stone/metals are not. Left-click orders construction on valid tiles. RMB or `Esc` cancels.
- Town Hall is unique and never appears as a placeable bottom-bar option.

### F-UI-TOP — Top Bar

- Fixed 48px strip. Shows population/housing as a clickable population-list entry, plus delivery queue/in-progress counts. It does not show resource rows or per-cycle income.

### F-UI-BOT — Bottom Bar (build menu)

- Fixed 96px strip with multi-level menu: Main → Resource / Social / Processing / Dev.
- Resource: `LUMBER_CAMP`, `STONE_MINE`, `IRON_MINE`, `FORESTER_HUT`, `WELL`.
- Food: food-source buildings and plots such as `FARM`, `FIELD`, `VINEYARD_FARM`, and `VINEYARD`.
- Processing: `SAWMILL`, `MILL`, `BAKERY`, `CHICKEN_FARM`, `COW_FARM`, `WINERY`. Social: `SCHOOL`, `HOUSE`, `CANTEEN`, `RESTAURANT`. Dev: place tree, stone, iron.
- Leaf clicks post placement intent. Buttons are gated by tech/state, not wallet affordability.

### F-UI-PANEL — Building Info Panel (modal)

- Left-click existing building opens a centered modal. Esc/close returns to normal view.
- Panel shows name + level, one-line description, relevant real local storage/input/output, stateful worker status, supported Upgrade, red Demolish, and close [×].
- Do not duplicate the same local stock with two counters. Upgrade is disabled at max level, under construction, or by explicit state gates such as non-empty School queue.
- Town Hall panel has no Demolish and no hiring. Hiring/training happens at School.
- Well panel shows **real** local water storage, assigned `WATERMAN` status, production/rest progress, active toggle where applicable, upgrade, and demolish—aligned with other staffed producers. Do not show carrier “draw” progress or well state derived from temporary carrier occupancy.
- Canteen panel shows real local food inputs, local meal stock, cook/production status, diner slots, and per-diner eating progress. Reserved/walking diners may be shown before they physically arrive, but must be visually distinguishable from diners already waiting or eating.
- Restaurant panel follows the same dining UI contract as Canteen but serves its configured advanced-tier meal and inputs.

### F-DEMO — Demolish

- **F-DEMO-01 (MUST):** Demolishing removes the building from the registry. No refund.
- **F-DEMO-02 (MUST):** If the demolished building had a worker, that worker becomes **idle** and visually stands at the building's former center tile until reassigned.

### F-UPG — Upgrade

- **F-UPG-01 (MUST):** Upgrade starts the next-level construction flow when configured in `CONSTRUCTION_REQUIREMENTS`. The building stays in-place, becomes inactive where applicable, receives a `ConstructionSite`, and increments `level` only when construction completes.
- **F-UPG-02 (MUST):** Upgrade orders do not spend from a wallet directly, but they are not “free completion”: carriers must deliver configured resources and builders must complete the build time. If a future UI label says “Free”, treat that as a bug unless the building truly has no requirements.
- **F-UPG-03 (MUST):** Building level effects for staffed workers come from that building's JSON under `worker_effects.by_level`. Effects apply only while the worker is assigned to that building and are additive with other bonuses.
- **F-UPG-04 (MUST):** Town Hall is **unique** (single instance, no demolish) **and** may **upgrade** levels 1..10 for tech and housing unlocks; only the no-second-TH rule is absolute.
- **F-UPG-05 (MUST):** `SCHOOL` cannot be upgraded while its training queue is non-empty. The upgrade button becomes enabled again as soon as the queue empties, whether by completed training or cancellation.

### F-CHAR — Worker Characteristics

- Workers expose `move_speed_mult` and `gather_speed_mult`, both starting at `1.0` and clamped positive.
- Bonuses are additive fixed-point modifiers. Permanent bonuses are tied to stable sources such as assigned building level; temporary bonuses expire at `now_ms >= expires_at_ms`.
- Test-visible bonus API: `add_permanent(source, kind, value)`, `add_temporary(kind, value, expires_at_ms)`, `remove_source(source)`.
- Level bonus source is `("building_level", building_id)`, with effect values loaded from the assigned building's `worker_effects.by_level` settings. Recompute on reassignment, demolition, and upgrade completion.
- Base action/rest durations still come from the assigned building's JSON. Worker characteristics modify effective runtime behavior; do not bake hunger, research, or level effects directly into the base JSON values.

### F-STORE — Internal Storage Contracts

- **F-STORE-01 (MUST):** Producer buildings expose local output storage for carrier pickup. Generic producers may use `stored` + `storage_capacity()` unless a building needs a specialized storage API; new producers should still expose local amount/capacity helpers needed by transport and UI.
- **F-STORE-02 (MUST):** Local storage capacities are per-building balance settings. Read them from that building's JSON under `src/game/settings/buildings/`; do not hard-code storage formulas in building classes when adding or changing buildings.
- **F-STORE-03 (MUST):** A worker assigned to a raw producer must not start a new gathering/harvest cycle when the relevant local output storage is full. The worker waits until carriers make space.
- **F-STORE-04 (MUST):** Processors can have separate local input and output storages:
  - `SAWMILL`: input wood, output boards.
  - `MILL`: input wheat, output flour.
  - `BAKERY`: input flour + water, output bread.
  - `CANTEEN`: local food/water inputs, local `simple_meal` output.
  - `RESTAURANT`: local premium food inputs, local `elite_meal` output.
  - `WINERY`: input grapes, output wine.
  - Animal farms use local input storage plus local output storage for their configured products.
- **F-STORE-05 (MUST):** Processor storage capacity follows each building's settings. Processors may have different input/output resources, but capacity tuning should live in the processor building JSON.
- **F-STORE-06 (MUST):** UI should show real local amounts only. Inbound/planned delivery counts are used for task planning but must not be displayed as already stored.

### F-HOUSING — Housing Capacity

- Each living worker occupies one housing slot.
- Town Hall and House housing capacity are per-level building settings in their building JSON files.
- New training/hire requests that would exceed capacity must be rejected with disabled/no-op UI.
- Population icon is disk-first with procedural fallback.

### F-SCHOOL-Q — School Training Queue

- Each `SCHOOL` has an independent FIFO queue. Queue capacity and training duration are configured in `school.json`. Ordering enqueues into the leftmost empty slot. Training is free but housing-gated.
- Only the front slot progresses. Completion spawns at that school, removes the icon, shifts the queue left, and restarts the new front from 0.
- School panel hiring controls are compact worker tiles with icon/avatar and label. The panel absorbs clicks across its whole frame.
- School hire tabs are driven by worker tier metadata from `game_settings.json` (`basic` / `advanced`). Add a new worker's tier and Town Hall hire gate there; keep workplace compatibility in code.
- School upgrade is blocked while any queue slot is occupied; completed training and cancellation both can unblock it.

### F-HOUSE — House (social)

- **F-HOUSE-01 (MUST):** Building type **`HOUSE`**, **2×2** footprint, levels **1..10**, placed from the **Social** submenu.
- **F-HOUSE-02 (MUST):** House upgrades follow normal construction/upgrade requirements when configured.
- **F-HOUSE-03 (MUST):** Demolishing a house reduces `max_population`; demolition must not leave `current_population > max_population`.

### F-WORK — Workers

- Current worker types include `CARRIER`, `BUILDER`, `LUMBERJACK`, `STONECUTTER`, `MINER`, `FARMER`, `FORESTER`, `SAWYER`, `MILLER`, `BAKER`, `COOK`, `WATERMAN`, `ANIMAL_HERDER`, and `WINEMAKER`. Staffed production workers only work in compatible buildings defined in code; worker tier and hire gate metadata live in `game_settings.json`.
- Workers are acquired only through School queue, respect housing, move with 4-direction BFS, never step onto blocking footprints, and are rendered with sprite interpolation.
- `WorkerManager.reassign_all()` runs after relevant state changes (training, construction, demolition, upgrade) to match idle compatible workers to unstaffed buildings.
- Production only happens when the worker state machine allows it. Town Hall has no worker slot.
- Cycles: stonecutter mirrors lumberjack on stones; forester plants; miner stays inside `IRON_MINE`; farmer works external `FIELD` tiles for `FARM` and `VINEYARD` plots for `VINEYARD_FARM`.
- Farmer target reservations prevent two farmers from sowing/harvesting the same field. Farm field radius is configured in `farm.json` and must be shared by runtime selection and placement-range UI. Builder exits completed regular buildings from the bottom; after completing `FIELD`, builder stays on that field tile.

### F-FOOD — Satiety, Canteens, And Dining

- **F-FOOD-01 (MUST):** Every worker has satiety that drains over game time and is visible in the worker panel. New workers start full; eating restores satiety to full. Global satiety values (`max`, drain rate, hunger threshold) live in `game_settings.json` under `workers.satiety`; do not hard-code them in dining or worker modules.
- **F-FOOD-02 (MUST):** Hungry workers may try to dine only at safe cycle boundaries: after completing or failing to start normal work, while idle, or after finishing a delivery/construction step. Carriers must not abandon carried resources, and builders must not abandon active construction. Internal retry throttles for blocked hunger checks may remain code-level mechanics.
- **F-FOOD-03 (MUST):** A worker should go to a compatible dining building only when that reachable building has both a free diner slot and an unreserved local meal for that worker's tier. Basic workers use Canteen/simple meals; advanced workers use Restaurant/elite meals. Reserving a dining trip reserves both the slot and the meal immediately, while visible local storage still shows only real stored meals.
- **F-FOOD-04 (MUST):** Dining has explicit worker-owned phases: going to the dining building, waiting/eating inside it, and returning to work. A reserved/walking diner occupies a slot for planning/UI, but eating starts only after physical arrival. Eating duration is building-specific balance under that building JSON's `dining.eat_duration_ms`.
- **F-FOOD-05 (MUST):** Meal assignment is one meal per worker. Normal dining dispatch reserves a meal before the worker leaves for the canteen, so more workers should not go eat than there are unreserved meals. If a waiting-diner state exists because of older state or edge-case recovery, assign meals deterministically by actual arrival/waiting order.
- **F-FOOD-06 (MUST):** After eating, a worker releases the canteen slot and walks back to the assigned workplace before resuming `working`. Do not teleport workers back to their buildings. If the worker's own workplace is the same canteen and the worker is already inside it, skip pointless pathing and resume locally.
- **F-FOOD-07 (MUST):** Dining reservation cleanup must run when a worker, canteen, or relevant building is demolished or invalidated so slots and reserved meals cannot remain stuck.

### F-PROD — Production

- **F-PROD-01 (MUST, **revised**):** Production is driven by worker cycles, not flat per-tick building income.
  - A completed gather/processing cycle produces discrete units (`+1` by building-specific rules), modulated by worker gather/processing speed bonuses.
  - No resource is generated while the worker is absent/resting/blocked or while storage constraints prevent cycle start.
- **F-PROD-02 (MUST):** Production is atomic per-cycle (no fractional accumulation).
- **F-PROD-03 (MUST):** Raw production fills source building internal output storage. Processor production consumes local inputs and fills local output storage.
- **F-PROD-03a (MUST):** Base action/rest or production/rest timing is building balance and belongs in that building's JSON. Runtime may apply worker modifiers such as speed effects to the effective duration, but the configured base values remain unmodified.
- **F-PROD-04 (MUST):** Current cycles:
  - Lumberjack/stonecutter gather from external resource tiles and return to camp/mine.
  - Miner stays inside `IRON_MINE`, producing into local storage through its configured work/rest cadence.
  - Sawyer/miller/baker must be assigned and inside their processor. Sawmill/mill/bakery use configured processing/rest cadence and local input requirements.
  - Cook must be assigned and inside `CANTEEN` or `RESTAURANT`; those buildings consume configured local inputs and produce their configured local-only meal.
  - `WATERMAN` must be assigned and inside a completed, active `WELL` with free local water storage; the well produces discrete `+1` water into that storage per configured cycle, then rests per `well.json`.
  - Farmer prioritizes ripe fields, then empty fields, within the configured radius from assigned farm. A farmer assigned to `VINEYARD_FARM` harvests ripe `VINEYARD` plots within that building's configured radius and deposits grapes into the farm's local storage.
- **F-PROD-05 (MUST):** Turning a processor inactive prevents new cycles and new input deliveries, but an already-started processing cycle may finish according to that building's existing runtime rule. Do not make active toggles delete in-flight carried resources.

### F-TRANSPORT — Carrier Logistics

- **F-TRANSPORT-01 (MUST):** Carriers execute `TransportTask(resource, source, target, priority)`. Construction delivery has higher priority than normal production logistics.
- **F-TRANSPORT-02 (MUST):** Production outputs are exported by carriers. If a processor with free input space exists for a compatible resource, carriers may deliver directly from producer output to processor input before Town Hall. Otherwise resources fall back to Town Hall warehouse where allowed.
- **F-TRANSPORT-03 (MUST):** Input-demand planning must account for already queued or in-flight deliveries so local input capacity is not overpromised. UI still displays only real stored local amounts.
- **F-TRANSPORT-04 (MUST):** Resource-to-processor routing should be capability based. For example wheat consumers expose `add_wheat_in` plus input amount/capacity; water consumers expose `add_water_in`, `water_amount`, `water_capacity`. Do not hard-code wheat to only `MILL`.
- **F-TRANSPORT-05 (MUST):** Water tasks are special only in that **no Town Hall water stock exists** and water must never be warehoused at Town Hall. Task sources are `WELL` instances with available **stored** water (same queue semantics as other local-storage pickups). Planning must count **queued and in-flight** outbound water from wells and inbound water to each consumer so capacities are not overpromised. Prefer reasonable nearest-well routing where practical. If a water source or consumer is demolished or becomes invalid while queued or in-flight, carriers must not trap state; carried water may be dropped, and invalid water must not be rerouted into Town Hall.
- **F-TRANSPORT-06 (MUST):** Carrier planning for dining-building inputs follows normal inbound-capacity rules for local inputs, but local-only meals such as `simple_meal` and `elite_meal` are never output transport tasks.

### F-INPUT — Input

- Left-click is primary action. RMB drag with 4px threshold pans camera; RMB click cancels placement/closes panel. `Esc` does the same cancel/close action.

---

## 3. Verification And Performance Notes

- Prefer focused pytest coverage for changed behavior plus `ruff check src tests`.
- Keep coverage strong around config, world generation/blocking, placement, workers, transport, and production loops.
- UI/asset tests run headless through `tests/conftest.py`.
- Renderer should stay camera-visible bounded. Worker dispatch should stay near O(buildings + active entities), not O(world width × height) per frame.
