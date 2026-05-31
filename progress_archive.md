# Progress Archive — Phases 1–12, 28, and 29

This archive holds the original detailed task lists for completed phases. The
live task tracker (`progress.md`) stays minimal once a phase is closed; full
task text for Phases 28–29 lives below.

All tasks below are `[x]` complete and documented here for traceability only —
ralph-loop must NOT re-run them. New work belongs to a fresh phase in
`progress.md`.

---

## Phase 1 — Project Foundation

- [x] **T01**: Create project skeleton — `src/game/`, `tests/`, `requirements.txt` (pygame 2.5.2, pytest 8.3.3, pyinstaller 6.10.0, ruff 0.6.9), `pyproject.toml`, `.gitignore`, empty `README.md`, empty `src/game/__init__.py`, `tests/__init__.py`. Verify `pip install -r requirements.txt` and `pytest -q` (0 tests, exits 0).
- [x] **T02**: Write `tests/conftest.py` setting `os.environ["SDL_VIDEODRIVER"]="dummy"` BEFORE any pygame import; autouse fixture init/quit pygame per session.
- [x] **T03**: Write `tests/test_config.py` asserting required constants (`TICK_MS=10_000`, `TILE_W=64`, `TILE_H=32`, `GRID_SIZE=32`, `INITIAL_RESOURCES=...`, etc.).
- [x] **T04**: Implement `src/game/config.py`.
- [x] **T05**: Write `tests/test_iso.py` covering round-trips for `world_to_screen`/`screen_to_world`.
- [x] **T06**: Implement `src/game/iso.py` with classic 2:1 isometric transform.
- [x] **T07**: Implement `src/game/main.py` (1280×720 pygame window, 60 FPS loop, clean shutdown).

## Phase 2 — Resources & Top Bar

- [x] **T08**: Write `tests/test_resources.py` (initial values, add, has, try_spend).
- [x] **T09**: Implement `ResourceManager` in `src/game/resources.py`.
- [x] **T10**: Write `tests/test_tick.py` covering 10 s tick boundary.
- [x] **T11**: Implement `TickScheduler` in `src/game/tick.py`.
- [x] **T12**: Implement `src/game/assets.py` (procedural sprite/icon factory, cached).
- [x] **T13**: Implement `src/game/ui/top_bar.py` (48 px strip with 4 resource entries).

## Phase 3 — World & Rendering

- [x] **T14**: `tests/test_world.py` — grid, occupancy, grass/tree zones.
- [x] **T15**: Implement `src/game/world.py` (`World` with grid + occupancy bitmap + grass/tree zones).
- [x] **T16**: Implement `src/game/render.py` `Renderer.draw_world` (grass diamonds + tree borders).
- [x] **T17**: Wire `World` + `Renderer` into `main.py`.

## Phase 4 — Buildings & Placement

- [x] **T18**: `tests/test_costs.py` covering `upgrade_cost(L)` for L=1..10 with stone@5+, iron@7+.
- [x] **T19**: Implement `src/game/buildings/costs.py`.
- [x] **T20**: `tests/test_buildings.py` per subclass (type, footprint, income, level cap).
- [x] **T21**: Implement `Building`, `TownHall`, `LumberCamp`, `StoneMine`, `IronMine`, `Farm`.
- [x] **T22**: `tests/test_registry.py` (placement validity, distance rule, second TH rejected).
- [x] **T23**: Implement `BuildingRegistry`.
- [x] **T24**: Implement `src/game/ui/bottom_bar.py` (4 build buttons, greyed when poor).
- [x] **T25**: Implement `src/game/ui/placement.py` (mouse-follow contour, click to place).

## Phase 5 — Building Panel & Actions

- [x] **T26**: Implement `BuildingPanel` (modal: name, level, description, income, status, actions, [×]).
- [x] **T27**: Wire click-on-building to open `BuildingPanel`; outside/[×] closes.
- [x] **T28**: Implement Upgrade action.
- [x] **T29**: Implement Demolish action (worker idle + parked at former center).
- [x] **T30**: Implement `TownHallPanel` (no demolish, hire buttons per worker type).

## Phase 6 — Workers

- [x] **T31**: `tests/test_workers.py` (hire deducts food, idle queue, type-matched assignment, demolition).
- [x] **T32**: Implement `Worker`, `WorkerManager` (hire, reassign_all, idle).
- [x] **T33**: Wire WorkerManager into game state.
- [x] **T34**: Render workers on screen (assigned dot, idle stack, orphans).
- [x] **T35**: Update Top Bar `+income`.
- [x] **T36**: Manual integration check.

## Phase 7 — Production, Polish, Package

- [x] **T37**: `tests/test_production.py` end-to-end.
- [x] **T38**: Implement production loop in `main.py` (or `game/loop.py`).
- [x] **T39**: Verify clean shutdown; `tests/test_shutdown.py`.
- [x] **T40**: Polish — FPS counter ≥ 55 with 50 buildings + 50 workers.
- [x] **T41**: `game.spec` + `build_exe.bat` for PyInstaller.
- [x] **T42**: Final `README.md`.

## Phase 8 — Render Fixes & Camera Pan

> Bugs A/B (Town Hall + new buildings invisible) + RMB drag camera.

- [x] **T43–T44**: `Renderer.draw_buildings` regression tests + implementation; wired into `main.py`.
- [x] **T45–T46**: `tests/test_camera.py` + `Camera` class with pan/clamp.
- [x] **T47**: Camera-aware rendering for world/buildings/workers/placement.
- [x] **T48**: `screen_to_grid` takes a `Camera`; tests for offset round-trip.
- [x] **T49**: RMB drag pan with 4 px threshold (`tests/test_rmb_drag.py`).
- [x] **T50**: World pixel bounds for clamping (`tests/test_world_bounds.py`).
- [x] **T51**: Smoke integration `tests/test_smoke_phase8.py`.

## Phase 9 — Worker Movement & Building Spacing

> 1 tile / 3 s walking; no stepping on buildings; 1-tile gap between footprints.

- [x] **T52–T53**: Spacing rule (Chebyshev ≥ 1) in registry.
- [x] **T54–T55**: `tests/test_worker_movement.py` + `Worker.update`/path queue.
- [x] **T56–T57**: `tests/test_pathfinding.py` + BFS in `src/game/pathfinding.py` (8-dir, no corner cutting, deterministic).
- [x] **T58**: Approach-tile selection in `WorkerManager.reassign_all`.
- [x] **T59**: Production gating via `working_buildings()`; demolition orphans worker.
- [x] **T60**: Smooth worker rendering (interpolated position).
- [x] **T61**: Wire `worker_manager.update(now_ms)` into `main.py`.
- [x] **T62**: `tests/test_smoke_phase9.py` end-to-end.

## Phase 10 — Tree Entities, Placement Clearing & Render Layering

> Trees become world-owned entities with growth stages; chopping is a future flow.

- [x] **T63–T64**: `tests/test_trees.py` + `src/game/trees.py` (`TreeStage`, `Tree`).
- [x] **T65–T66**: World owns trees by tile; sparse groves + scatter (see F-WORLD-02), center clearing.
- [x] **T67–T68**: BFS treats alive tree tiles as blocked; movement detours.
- [x] **T69–T70**: Placement clears trees inside the new footprint.
- [x] **T71–T72**: Tree assets per stage; loader with procedural fallback.
- [x] **T73–T74**: Render layering — trees draw above buildings/workers behind them.

## Phase 11 — Lumberjack Chop Cycle

> Lumber Camp no longer passively produces wood. A staffed Lumber Camp dispatches
> its Lumberjack on a chop cycle: walk to a free tree → adjacent free tile →
> chop for 10 s → carry wood back to the camp → deposit `+1 wood` and remove the
> tree. Active/Inactive toggle on the camp; `delivered_wood` counter; `carrying`
> flag on the worker. Two distinct lumberjack sprites (empty / carrying).
> Lumberjack rests inside the camp for `LUMBERJACK_REST_MS = 5000 ms` between
> trips and stays parked inside if the camp is toggled off.

- [x] **T75–T91** — full coverage in `tests/test_lumber_camp_state.py`,
  `test_lumberjack_cycle_states.py`, `test_lumber_camp_active_toggle.py`,
  `test_smoke_phase11.py`, etc.

## Phase 12 — Level Bonuses, Internal Storage, Stones

> Per-level bonuses replace passive income for `LUMBER_CAMP` and `STONE_MINE`.
> Workers gain a `Characteristics` block (additive `move_speed_mult`,
> `gather_speed_mult`, +5 % per level above 1, sourced as
> `("building_level", id(building))` so they can be removed atomically). All
> producing buildings get an internal `stored / capacity(L)` slot
> (`capacity(L) = 3 + 2 × (L − 1)`); workers stop launching new gather cycles
> when storage is full. Stones are world entities with 15 units each, generated
> in 3 random clusters at Chebyshev ≥ 12 from the Town Hall, radius
> `r ∈ [1, 4]`, blocking movement and placement; they never share a tile with a
> tree. Stonecutters mirror the lumberjack chop cycle.

- [x] **T92–T125** — full coverage in `tests/test_worker_characteristics.py`,
  `test_workers.py`, `test_worker_movement.py`, `test_lumberjack_speed_bonus.py`,
  `test_registry.py`, `test_buildings.py`, `test_lumberjack_cycle_deposit.py`,
  `test_production.py`, `test_lumber_camp_panel.py`,
  `test_building_panel_storage.py`, `test_stones.py`, `test_world.py`,
  `test_pathfinding.py`, `test_render_stones.py`, `test_stone_mine_state.py`,
  `test_stonecutter_cycle.py`, `test_stone_mine_panel.py`, `test_assets.py`,
  `test_smoke_phase12.py`. HF12-A regression preserved in
  `test_lumber_camp_panel.py::test_lumber_camp_click_upgrade_returns_upgrade_not_demolish`.

---

## Decisions kept from old log

- Stone +200/level from L5, iron +300/level from L7 mirror the wood pattern.
- Worker hire cost fixed at 50 food (later moved to `game_settings.json` and reduced to 5).
- All assets are procedural fallback; binary placeholders OK once `asset_meta.json` carries scale/anchor.
- Tests run headless via `SDL_VIDEODRIVER=dummy`.

---

## Phase 28 - Laboratory and Research

**Goal.** Add a unique `LABORATORY` social building, a new advanced `SCIENTIST` worker, and a research system opened from the top bar after a completed Laboratory exists. Researches are configured in JSON, require delivered resources, progress through research points produced by active Scientists inside the Laboratory, and are displayed in a full-screen research menu organized into four technology tiers.

**Ralph-loop task rules for this phase.**

- Each task must be independently finishable in one iteration.
- Each task should change one behavior, one integration point, or one narrow data surface.
- Each task includes its own focused tests and must leave full `pytest` plus `ruff check src tests` passing before it is marked `[x]`.
- Do not add intentionally failing tests as a separate checked task.
- Do not combine schema/data creation, runtime integration, UI behavior, and transport behavior in one task.

**Design notes.**

- Building type: `LABORATORY`.
- Menu category: Social.
- Building uniqueness: only one Laboratory may exist or be under construction at a time.
- Worker type: `SCIENTIST`.
- `SCIENTIST` is hired in School under the `advanced` tab.
- Laboratory staffing is not the normal one-worker model:
  - level 1-2: 1 Scientist slot;
  - level 3-4: 2 Scientist slots;
  - level 5-6: 3 Scientist slots;
  - level 7-8: 4 Scientist slots;
  - level 9-10: 5 Scientist slots.
- Only Scientists assigned to the Laboratory and currently working/inside count toward research speed. Scientists who are dining, walking, idle, or otherwise away from the Laboratory do not contribute points.
- Research speed is point based. Each active Scientist contributes configured research points per game second. Multiple Scientists scale linearly.
- Research data lives in a dedicated JSON file. Each research entry must define:
  - stable `id`;
  - display name/description;
  - tier row `1..4`;
  - explicit column;
  - required research points;
  - resource cost map;
  - dependency id list;
  - image asset key/path.
- The four static Technology researches are part of that JSON. Their IDs are `1`, `2`, `3`, and `4`; they are placed in the left/static column, one per tier, and each higher Technology depends on the previous Technology.
- Laboratory level gates Technology tier availability:
  - Laboratory level 1 unlocks Technology tier 1;
  - Laboratory level 3 unlocks Technology tier 2;
  - Laboratory level 6 unlocks Technology tier 3;
  - Laboratory level 9 unlocks Technology tier 4.
- A non-Technology research may also have dependencies from any earlier completed researches listed in JSON. Do not hard-code dependency chains in Python.
- Starting a research selects it as the only active research. It cannot be cancelled.
- Starting a research creates dynamic local input storage in the Laboratory exactly for the selected research's resource cost. The UI shows only real delivered amounts, not queued/in-flight amounts.
- Research points begin only after all required resources have been delivered to the Laboratory local input storage.
- Carrier planning for Laboratory inputs must account for queued/in-flight deliveries so the dynamic storage is not overfilled.
- If any research is active, every other research start button is disabled.
- The full-screen Research menu has four equal-height rows. Tiles are placed by configured tier row and column.
- Each research tile shows an image. The same image is shown in the Laboratory panel when that research is active.
- A tile is full-color only when completed. Not-started and in-progress tiles are dimmed/partially transparent.
- Each tile has a start button directly below it with a small gap. The button is active only when the research can currently start.
- Hovering a research tile shows a compact tooltip with resource cost, point requirement, dependencies, and lock reason where relevant.
- The Laboratory panel shows active research image, dynamic input storage, total research progress bar, and numeric points such as `350 / 10000`.
- Research completion persists in memory for the current run. Save/load is still out of scope.
- This phase implements the framework and required Technology researches. Concrete gameplay effects for future non-Technology researches are out of scope until their list/effects are specified.
- Balance/configuration values belong in JSON. Tests must check behavior and schema, not exact balance numbers.

### 28.1 Research Data Foundation

- [x] **T387**: Add research config JSON only. Create a dedicated research settings file with the four Technology entries (`id` values `1`, `2`, `3`, `4`), tier rows, explicit columns, dependencies, resource cost maps, point requirements, and image keys. Do not add a Python loader yet. Add focused tests that parse the JSON and assert the four Technology entries have the required fields and dependency chain. Run full `pytest` and `ruff check src tests`.
- [x] **T388**: Add research config loader and validation only. Create a small domain loader for the JSON from T387 that validates unique ids, tier range, column presence, cost shape, positive point requirement, image key presence, and dependency references. Do not add mutable research state yet. Add focused loader/validation tests. Run full `pytest` and `ruff check src tests`.
- [x] **T389**: Add research domain state only. Create an in-memory state/service that tracks completed research ids, active research id, delivered resource amounts for the active research, and accumulated research points. Do not add UI, transport, building integration, or point production yet. Add focused tests for starting state, completion marking, active research exclusivity, and delivered/progress bookkeeping. Run full `pytest` and `ruff check src tests`.
- [x] **T390**: Add research asset placeholder files only. Create the research asset folder and placeholder image files for the four Technology researches. Do not add new asset helper code yet. Add focused filesystem/config consistency tests proving configured image keys have placeholder files. Run full `pytest` and `ruff check src tests`.
- [x] **T391**: Add research asset resolver only. Add an asset helper that resolves research images disk-first and falls back procedurally when missing. Do not render research UI yet. Add focused asset tests proving configured research image keys resolve without crashing. Run full `pytest` and `ruff check src tests`.

### 28.2 Laboratory Building Foundation

- [x] **T392**: Add only `src/game/settings/buildings/laboratory.json`. Include `LABORATORY`, footprint, 10 construction/upgrade levels, scientist slot capacity by level, research points per Scientist per second, tech-tier unlock level mapping, worker effects if any, and asset metadata. Use JSON for all balance values. Add focused settings tests proving values are loaded from this JSON. Run full `pytest` and `ruff check src tests`.
- [x] **T393**: Add only the `Laboratory` building class shell. Define `type_tag`, normal `Building` contract, scientist slot capacity helper, research-point-rate helper, tech-tier unlock helper, and empty dynamic research-storage helpers. Do not register placement, menu, UI, workers, transport, or research runtime yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T394**: Register `LABORATORY` for placement and construction only. Wire the class into placement maps and construction config usage so it can be placed and built. Do not add menu visibility, worker assignment, top-bar button, research UI, or transport. Add focused placement/construction tests. Run full `pytest` and `ruff check src tests`.
- [x] **T395**: Enforce Laboratory uniqueness only. Prevent placing a second Laboratory while one exists or is under construction, while preserving normal placement for other buildings. Add focused placement/registry tests. Run full `pytest` and `ruff check src tests`.
- [x] **T396**: Add Laboratory building asset loading/fallback only. Add building folder mapping and placeholder/meta files only if real assets are absent; add focused asset tests proving construction and completed sprites resolve. Run full `pytest` and `ruff check src tests`.
- [x] **T397**: Add Laboratory to the Social build menu only. Add the Social menu tile/click routing for `LABORATORY` and focused bottom-bar/input tests that avoid brittle coordinate assertions where possible. Run full `pytest` and `ruff check src tests`.
- [x] **T398**: Add Laboratory display labels/descriptions only. Update building display names/descriptions and construction panel display name. Add focused label tests. Run full `pytest` and `ruff check src tests`.

### 28.3 Scientist Worker and Laboratory Staffing

- [x] **T399**: Add `SCIENTIST` hire metadata only. Update worker tier metadata in `game_settings.json` and Town Hall hire gate metadata so `SCIENTIST` is recognized as an advanced hireable worker. Do not add icons, labels, School UI assertions, or building compatibility yet. Add focused metadata/hiring tests. Run full `pytest` and `ruff check src tests`.
- [x] **T400**: Add Scientist display assets/labels only. Add worker label/icon/procedural fallback coverage needed for UI rendering. Do not change School tab logic or building compatibility. Add focused display/asset tests. Run full `pytest` and `ruff check src tests`.
- [x] **T401**: Add Scientist to School advanced-tab UI only. Ensure the School advanced hiring tab shows `SCIENTIST` and can enqueue training through existing School queue behavior. Do not assign Scientists to buildings yet. Add focused School panel/queue tests. Run full `pytest` and `ruff check src tests`.
- [x] **T402**: Add Scientist-to-Laboratory compatibility only. Update worker compatibility rules so `SCIENTIST` is compatible with `LABORATORY`, without changing one-worker assignment semantics yet. Add focused compatibility tests. Run full `pytest` and `ruff check src tests`.
- [x] **T403**: Add Laboratory multi-slot counting helpers only. Add WorkerManager helpers that count Scientists assigned to a Laboratory and report free Scientist slots from Laboratory capacity. Do not change automatic assignment yet. Add focused helper tests using manual workers/buildings. Run full `pytest` and `ruff check src tests`.
- [x] **T404**: Add automatic assignment of multiple Scientists to one Laboratory only. `WorkerManager.reassign_all()` should assign idle Scientists into free Laboratory slots up to capacity, while preserving one-worker assignment behavior for normal buildings. Add focused assignment tests for levels with different slot counts. Run full `pytest` and `ruff check src tests`.
- [x] **T405**: Add Laboratory demolition cleanup for Scientists only. When the Laboratory is demolished, assigned Scientists become idle and do not retain a stale assignment. Do not handle upgrades in this task. Add focused demolition lifecycle tests. Run full `pytest` and `ruff check src tests`.
- [x] **T406**: Add Laboratory upgrade/construction pause behavior for Scientists only. While the Laboratory is under construction/upgrading, Scientists should not contribute or appear as active workers; after completion, reassignment may fill available slots. Add focused upgrade/construction lifecycle tests. Run full `pytest` and `ruff check src tests`.
- [x] **T407**: Add Laboratory panel Scientist slot display only. Show Scientist slots and assigned/empty state in the Laboratory panel without adding active research display yet. Add focused panel layout/draw tests. Run full `pytest` and `ruff check src tests`.

### 28.4 Top Bar and Research Screen Shell

- [x] **T408**: Add top-bar Research button visibility only. Show the "Research" button only when a completed Laboratory exists; hide it while no Laboratory exists or the Laboratory is under construction. Do not open a screen yet. Add focused top-bar tests. Run full `pytest` and `ruff check src tests`.
- [x] **T409**: Add Research screen open/close shell only. Clicking the top-bar Research button opens a full-screen modal overlay; close/Esc returns to the game. Do not draw research rows or tiles yet. Add focused input/modal tests. Run full `pytest` and `ruff check src tests`.
- [x] **T410**: Add four-row research screen layout only. Draw four equal-height tier rows and a left static Technology column area using configured row positions. Do not add research tiles, start buttons, or eligibility yet. Add focused layout tests. Run full `pytest` and `ruff check src tests`.
- [x] **T411**: Add research tile rendering only. Render configured research tiles at their configured tier/column with image and title. Do not add dim/full-color completion state or clickable start buttons yet. Add focused draw/layout tests. Run full `pytest` and `ruff check src tests`.
- [x] **T412**: Add research tile completion visual state only. Completed research tiles render full-color; not-started and in-progress tiles render dimmed/partially transparent. Do not add start buttons yet. Add focused rendering tests. Run full `pytest` and `ruff check src tests`.
- [x] **T413**: Add per-tile Start button rendering only. Render a button directly below each tile with the required spacing, visually enabled/disabled from a supplied eligibility flag. Do not handle clicks yet. Add focused layout tests. Run full `pytest` and `ruff check src tests`.
- [x] **T414**: Add research requirement tooltip only. Hovering a research tile should show a compact tooltip with configured cost, required points, dependencies, and lock reason text supplied by eligibility logic. Do not start research from the tooltip. Add focused UI tests. Run full `pytest` and `ruff check src tests`.

### 28.5 Research Eligibility and Start Flow

- [x] **T415**: Add base research eligibility rules only. Implement pure/domain checks for: completed research cannot start, active research blocks all starts, and a completed Laboratory must exist. Do not add level-tier gates or dependency gates yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T416**: Add Laboratory level tier gates only. Extend eligibility so Laboratory level unlocks research tiers according to Laboratory settings. Do not add dependency gates yet. Add focused eligibility tests for levels 1, 3, 6, and 9. Run full `pytest` and `ruff check src tests`.
- [x] **T417**: Add research dependency gates only. Extend eligibility so configured dependency ids must be completed before a research can start. Do not add UI button wiring yet. Add focused dependency tests. Run full `pytest` and `ruff check src tests`.
- [x] **T418**: Add research config validity checks to eligibility only. Ensure researches with invalid/empty cost shape or non-positive point requirements are treated as non-startable with a clear lock reason, even if the loader normally prevents them. Add focused defensive tests. Run full `pytest` and `ruff check src tests`.
- [x] **T419**: Wire Research screen button enabled state to eligibility only. Disabled buttons should be grey/transparent and non-startable; enabled buttons should look active. Do not mutate active research on click yet. Add focused UI tests. Run full `pytest` and `ruff check src tests`.
- [x] **T420**: Add domain start-active-research behavior only. Starting an eligible research should set the active research id and reject starting any other research while one is active. Do not create dynamic input storage yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T421**: Add dynamic input storage creation on research start only. When research starts, initialize Laboratory dynamic input storage exactly for that research's cost map with zero delivered amounts. Do not wire UI clicks yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T422**: Wire Start button click to domain start only. Clicking an eligible Start button should call the domain start flow and leave the selected research uncancellable. Do not add carrier delivery yet. Add focused input/domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T423**: Add Laboratory dynamic input storage display only. Laboratory panel should show the active research image and one row per required input resource with real delivered amount/capacity. Do not add carrier delivery or point progress yet. Add focused panel tests. Run full `pytest` and `ruff check src tests`.

### 28.6 Research Resource Logistics

- [x] **T424**: Add Laboratory input-demand planning only. For the active research, carriers should create tasks from Town Hall to Laboratory for required warehouse resources, accounting for already delivered, queued, and in-flight amounts. Do not deliver resources yet. Add focused transport planning tests. Run full `pytest` and `ruff check src tests`.
- [x] **T425**: Add carrier delivery into Laboratory dynamic storage only. Carriers should deliver research input resources into the Laboratory's active research storage and reject overfill/irrelevant resources. Add focused delivery tests. Run full `pytest` and `ruff check src tests`.
- [x] **T426**: Add invalidation handling for active research deliveries only. If the Laboratory is demolished while research inputs are queued or in-flight, normal carried resources should return to Town Hall using existing invalid-delivery semantics, and the active research should not trap carriers. Add focused edge-case tests. Run full `pytest` and `ruff check src tests`.
- [x] **T427**: Add "resources delivered" gate only. Research point production must not start until every required resource amount for the active research has been delivered. Add focused domain/runtime tests with no Scientist timing behavior beyond stubs. Run full `pytest` and `ruff check src tests`.

### 28.7 Research Point Runtime and Completion

- [x] **T428**: Add single-Scientist research point production only. With one assigned Scientist inside a completed Laboratory and all resources delivered, accumulate points over elapsed game time using configured points-per-second. Do not handle multiple Scientists yet. Add focused runtime tests. Run full `pytest` and `ruff check src tests`.
- [x] **T429**: Add multi-Scientist linear scaling only. Accumulated points should scale linearly with the number of active Scientists inside the Laboratory, up to Laboratory slot capacity. Add focused runtime tests for two and max-capacity Scientists. Run full `pytest` and `ruff check src tests`.
- [x] **T430**: Exclude absent/dining Scientists from research speed only. Scientists who are dining, walking to eat, returning from dining, idle, unassigned, or otherwise not active inside the Laboratory should not contribute points. Add focused runtime tests. Run full `pytest` and `ruff check src tests`.
- [x] **T431**: Add research completion only. When accumulated points reach the configured requirement, mark the research complete, clear active research/dynamic input storage/progress, and allow the next eligible research to start. Add focused completion tests. Run full `pytest` and `ruff check src tests`.
- [x] **T432**: Add Technology chain unlock behavior only. Completing Technology `1` should allow eligible tier-2 researches when Laboratory level permits, and so on through Technology `4`. Add focused eligibility tests for dependency and Laboratory-level gates. Run full `pytest` and `ruff check src tests`.

### 28.8 Research Progress UI Integration

- [x] **T433**: Add Laboratory active research progress UI only. Laboratory panel should show active research image, progress bar, and numeric points like `350 / 10000` once the research has started. Add focused panel tests. Run full `pytest` and `ruff check src tests`.
- [x] **T434**: Add Research screen active progress state only. The full-screen Research menu should visually mark the currently active research as in-progress. Do not change completed/not-started state from earlier rendering. Add focused UI tests. Run full `pytest` and `ruff check src tests`.
- [x] **T435**: Add top-bar Research button state refresh only. The button should appear/disappear correctly after Laboratory construction completion, demolition, and rebuild, without requiring restart. Add focused integration tests. Run full `pytest` and `ruff check src tests`.

### 28.9 Integration and Documentation

- [x] **T436**: Add one bounded end-to-end Laboratory/Research integration test only.
- [x] **T437**: Update Laboratory/Research documentation only.
- [x] **T438**: Close Phase 28 progress only. After every Phase 28 task is `[x]`, update Current Status, Last Completed, Total Progress, Decisions Log, Notes, and archive/phase-completion wording as needed. Do not add feature code in this task. Run final full `pytest` plus `ruff check src tests`; mark Phase 28 complete only when all checks pass.

---


## Task Log

**Phase 29 - Localization EN/RU** migrates player-facing text out of Python/runtime balance files into dedicated locale files. Initial supported languages are English (`en`) and Russian (`ru`). Locale files must live under **`src/game/settings/locales/`**. Keep gameplay/balance JSON separate from translatable copy where practical.

### Phase 29 working agreement (read before every task)

Each task runs in a fresh context. Do not assume prior memory; read this block, the task text, and the named files from disk.

- **i18n entry point:** all player-facing strings render through `game.i18n.t(key, **params)` (created in T441). Never re-introduce raw literals in UI/runtime once a module is migrated.
- **Key naming convention** (defined in T439, used by all later tasks):
  - `ui.button.<name>` (e.g. `ui.button.start`, `ui.button.upgrade`, `ui.button.demolish`, `ui.button.close`, `ui.button.back`)
  - `ui.common.<name>` (e.g. `ui.common.active`, `ui.common.inactive`, `ui.common.cost`, `ui.common.status`, `ui.common.storage`, `ui.common.requirements`)
  - `resource.<id>` (e.g. `resource.wood`, `resource.simple_meal`)
  - `worker.<TYPE>` (e.g. `worker.CARRIER`)
  - `building.<TYPE>.name`, `building.<TYPE>.desc`
  - `status.<id>` for production/worker statuses (e.g. `status.ready`, `status.output_full`)
  - `research.<id>.name`, `research.<id>.desc`, `research.<id>.effect`
  - `statue.stage.<n>` (n = 1..4)
- **Counts use `label: N` format** (e.g. `Дерево: 34`). No grammatical pluralization.
- **ids/enums never change.** Only the displayed text moves to locales. Resource keys, `type_tag`s, worker/state ids, research ids stay as-is.
- **Backpressure (run before marking any task `[x]`):**
  - Targeted: `pytest -q tests/<file>.py` for the tests named in the task.
  - Full suite: `pytest -q` (must stay green; default locale is `en`).
  - When adding new files: `ruff check src tests`.
  - Tests are headless (`SDL_VIDEODRIVER=dummy` via `tests/conftest.py`); the default test locale is `en` unless a test explicitly switches it via the T442 harness.
- **Locale switching in tests** must use the T442 harness (no leaking global locale state across tests).
- **Fallback:** missing `ru` key → fall back to `en`; missing `en` key → return the key id (loud, so it is caught).

- [x] **T439**: Define i18n key schema and contract (design + tiny validation test).
  - Write the contract as a short doc section in `localization_guide.md` (new file at repo root) capturing the key naming convention from the working agreement above, `{param}` placeholder syntax, and fallback rules (`ru`→`en`→key id).
  - Decide JSON shape: nested objects keyed by dotted segments OR flat dotted keys. Pick **flat dotted keys** (e.g. `"ui.button.start": "Start"`) for simple diffing and completeness checks; record this choice.
  - Create empty/seed `src/game/settings/locales/en.json` and `src/game/settings/locales/ru.json` containing only 2-3 sample keys (`ui.button.start`, `resource.wood`, `research.1.name`) to prove the shape can express button, resource, and research copy.
  - Add `tests/test_i18n_schema.py` that loads both files as JSON, asserts they parse, and asserts the sample keys exist in both.
  - Verify: `pytest -q tests/test_i18n_schema.py`; `ruff check src tests`; then `pytest -q`.
  - Acceptance: schema doc exists, both locale files parse, sample-key test passes.
- [x] **T440**: Add failing loader tests for `game.i18n` (RED).
  - Create `tests/test_i18n_loader.py` covering: load default locale (`en`), load explicit locale (`ru`), `t("ui.button.start")` returns the English string, `t(<key only in en>)` from `ru` falls back to English, `t(<missing key>)` returns the key id, and `{param}` substitution via `t("x.y", name="Дерево")`.
  - These tests import `from game import i18n` which does not exist yet, so they must fail (RED). Do not implement the module in this task.
  - Verify: `pytest -q tests/test_i18n_loader.py` and confirm it fails for the expected (import/attribute) reason, not a syntax error in the test.
  - Acceptance: `test_i18n_loader.py` exists and is RED; the rest of the suite is unaffected (`pytest -q` shows only these new failures).
- [x] **T441**: Implement `game.i18n` loader + current-locale selection (GREEN).
  - Create `src/game/i18n.py` with: `t(key: str, **params) -> str`, `set_locale(code: str)`, `get_locale() -> str`, and a loader that reads `src/game/settings/locales/<code>.json`.
  - Default locale comes from a new optional `"locale"` key in `game_settings.json` (add `"locale": "en"`), defaulting to `en` when absent.
  - Fallback chain: requested locale → `en` → return key id. `{param}` substitution via `str.format(**params)`; on `KeyError`/missing param, return the unformatted template (do not crash).
  - Make all `test_i18n_loader.py` tests from T440 pass.
  - Verify: `pytest -q tests/test_i18n_loader.py tests/test_i18n_schema.py`; `ruff check src tests`; then `pytest -q`.
  - Acceptance: loader tests are GREEN and full suite passes.
- [x] **T442**: Add a locale-switch test harness (used by all later `ru`-smoke tests).
  - Add a pytest fixture/context manager in `tests/conftest.py` (e.g. `use_locale`) that calls `i18n.set_locale(code)` and restores the previous locale on exit, so no global locale state leaks between tests.
  - Add `tests/test_i18n_harness.py` proving the same key returns English then Russian inside two isolated `use_locale` blocks, and that the locale is restored to `en` afterward.
  - Verify: `pytest -q tests/test_i18n_harness.py`; then `pytest -q`.
  - Acceptance: harness exists, isolation test passes, no other test changes behavior.
- [x] **T443**: Centralize font creation and bundle a Cyrillic-capable font.
  - Create `src/game/ui/fonts.py` with a cached helper `ui_font(size: int) -> pygame.font.Font` that loads one bundled TTF by path.
  - Add a Unicode TTF with full Cyrillic coverage under `assets/fonts/` (e.g. DejaVuSans). Load it relative to the package, falling back to `pygame.font.Font(None, size)` only if the file is missing.
  - Replace every `pygame.font.Font(None, size)` call in `src/game/ui/*.py`, `src/game/render.py`, and `src/game/assets.py` with `ui_font(size)`. (Use `rg "Font\(None" src` to find all sites.)
  - No packaging step is required: delivery is via `run.bat` (runs from source with `PYTHONPATH=src`). The optional `game.spec`/`build_exe.bat` build is not the actual delivery path and bundles no `datas`.
  - Add `tests/test_ui_fonts.py`: `ui_font(22).render("Дерево", True, (255,255,255))` returns a surface with `get_width() > 0`, and confirm no `Font(None` remains via the test or a documented allowlist.
  - Verify: `pytest -q tests/test_ui_fonts.py`; `ruff check src tests`; then `pytest -q`.
  - Acceptance: Cyrillic renders to a non-empty surface; all panels use `ui_font`; full suite passes.
- [x] **T444**: Seed shared/common locale keys (`ui.*`).
  - Add to both locale files: `ui.button.{start,upgrade,demolish,close,back}`, `ui.common.{active,inactive,cost,status,storage,requirements,free,unavailable}`, and `ui.window.caption` (en: `Isometric Strategy`). Provide Russian values for all.
  - Apply `ui.window.caption` in `main.py` (replace the literal in `pygame.display.set_caption(...)` with `i18n.t("ui.window.caption")`).
  - Verify: `pytest -q tests/test_i18n_schema.py`; smoke `python -c "import game.main"`; then `pytest -q`.
  - Acceptance: both files contain all listed keys with non-empty values; caption uses i18n.
- [x] **T445**: Migrate resource display labels (`resource.<id>`) — `src/game/resource_catalog.py`.
  - Replace the body of `resource_display_label` and `_DISPLAY_LABEL_OVERRIDES` with an i18n lookup: `t(f"resource.{key}")`, where `key` is the lowercased resource id; keep current fallback (`key.replace("_"," ").title()`) when the locale has no entry.
  - Add `resource.*` keys to both locales for every id in `TOWN_HALL_WAREHOUSE_KEYS` plus `simple_meal`, `elite_meal`, `water` (en values: current Title-Case; `Simple meal`, `Elite meal`).
  - Update/extend `tests/test_elite_meal_resource.py`; cover `wood`, `simple_meal`, `elite_meal`, and an unknown id fallback, with a `ru` smoke using the harness.
  - Verify: `pytest -q tests/test_elite_meal_resource.py`; then `pytest -q`.
  - Acceptance: labels come from locales; ids unchanged; tests pass `en`+`ru`.
- [x] **T446**: Migrate worker display labels (`worker.<TYPE>`) — `src/game/ui/worker_labels.py`.
  - Replace `WORKER_LABEL` dict usage in `worker_display_label` with `t(f"worker.{key}")`, keeping the `.title()` fallback. Keep `building_worker_status_line` format but route the `Worker`/`Worker (label)` words through `ui.*`/`worker.*` keys.
  - Add `worker.<TYPE>` keys to both locales for every type in `WORKER_LABEL` (all 15 listed).
  - Update `tests/test_winemaker_display.py` and `tests/test_scientist_display.py`; add a parametrized test covering every `HIRABLE_WORKERS` type in `en` and `ru`.
  - Verify: `pytest -q tests/test_winemaker_display.py tests/test_scientist_display.py`; then `pytest -q`.
  - Acceptance: every worker type has localized labels in both locales; tests pass.
- [x] **T447**: Migrate building names + descriptions (`building.<TYPE>.name/.desc`) — `src/game/ui/building_panel.py`.
  - Replace `_DISPLAY_NAME` and `_DESCRIPTION` lookups with `t(f"building.{tag}.name")` / `t(f"building.{tag}.desc")`.
  - Add `building.<TYPE>.name` and `.desc` keys for every registered building type (the 17 names in `_DISPLAY_NAME` plus `MILL`, which has a description but no name entry — add a `MILL` name). Use existing English strings verbatim.
  - Update `tests/test_building_panel.py`; assert localized name/desc for at least `TOWN_HALL`, `LABORATORY`, `STATUE` in `en` and one `ru` smoke.
  - Verify: `pytest -q tests/test_building_panel.py`; then `pytest -q`.
  - Acceptance: all building types resolve a non-empty localized name; tests pass.
- [x] **T448**: Localize bottom build menu + cost tooltip — `src/game/ui/bottom_bar.py`.
  - Route category/building button labels (`_RESOURCE_BUTTONS`, `_FOOD_BUTTONS`, and the inline lists `School/House/Canteen/Restaurant/Laboratory/Statue`, `Sawmill/Mill/Bakery/...`) through `building.<TYPE>.name` (T447) so labels are not duplicated.
  - Route the cost tooltip words `Cost:`, `Cost: Free`, `Cost: unavailable` through `ui.common.*` keys; keep `{resource_display_label}: {n}` lines.
  - Localize the statue research requirement line text.
  - Update `tests/test_bottom_bar_menu.py`; assert English defaults and a `ru` lookup smoke.
  - Verify: `pytest -q tests/test_bottom_bar_menu.py`; then `pytest -q`.
  - Acceptance: bottom-bar labels/tooltips come from locales; tests pass.
- [x] **T449**: Localize top bar — `src/game/ui/top_bar.py`.
  - Replace `_RESEARCH_BTN_LABEL = "Research"` with `t("ui.topbar.research")`; template the population label `"{current} (max {max})"` and the deliveries label `"Deliveries: {n} (in progress {k})"` via i18n templates with `{param}` placeholders.
  - Add `ui.topbar.*` keys (research button, population template, deliveries template) to both locales.
  - Update the top-bar layout test (find via `rg "TopBar" tests`); assert layout still computes and `{param}` substitution is exercised in `en` and `ru`.
  - Verify: run the top-bar test file; then `pytest -q`.
  - Acceptance: top-bar text from locales; layout tests pass; templates tested.
- [x] **T450**: Localize base building panel actions + Town Hall panel.
  - In `building_panel.py`: route `_upgrade_label` (`Start stage: {stage}`, `Upgrade to Lv {n}`), `_upgrade_cost_lines` words, demolish/close/status/storage words, and the statue stage upgrade text through `ui.*`/`building.*`/`statue.*` keys.
  - In `src/game/ui/town_hall_panel.py`: route the panel title and warehouse resource labels through `building.TOWN_HALL.name` / `resource.<id>`.
  - Update `tests/test_building_panel.py` and `tests/test_town_hall_panel.py`; cover upgrade label for a normal building and the statue stage label.
  - Verify: `pytest -q tests/test_building_panel.py tests/test_town_hall_panel.py`; then `pytest -q`.
  - Acceptance: building-panel, town-hall-panel, and statue-panel tests pass with localized text.
- [x] **T451**: Localize construction panel — `src/game/ui/construction_panel.py`.
  - Route title line, requirements header, delivered counters, builder state, progress, demolish, active/inactive, and the statue delivery toggle through `ui.*`/`status.*`/`statue.*` keys; keep numeric `{n}/{m}` formats.
  - Update `tests/test_*construction*` (find via `rg -l construction tests`); cover a regular building and statue construction in `en`, plus one `ru` smoke.
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: construction-panel tests pass for regular + statue.
- [x] **T452**: Localize worker panel — `src/game/ui/worker_panel.py`.
  - Route state labels, satiety, movement speed, assignment, carrying, task, from/to, returning, and resource names through `status.*`/`ui.*`/`resource.*`/`worker.*` keys.
  - Update the worker-panel test (find via `rg -l worker_panel tests`); add a `ru` smoke for one worker.
  - Verify: run the worker-panel test file; then `pytest -q`.
  - Acceptance: worker-panel tests pass; one `ru` smoke included.
- [x] **T453**: Localize population panel — `src/game/ui/population_panel.py`.
  - Route title, filters, worker rows, assignment/task detail labels, and any empty-state text through `ui.*`/`status.*`/`worker.*` keys (note the local `"sowing": "Sowing"` style map at the top of the module).
  - Update the population-panel test (find via `rg -l population_panel tests`); ensure click/scroll behavior tests do not regress.
  - Verify: run the population-panel test file; then `pytest -q`.
  - Acceptance: population-panel tests pass; interaction behavior unchanged.
- [x] **T454**: Externalize production/worker status strings (`status.<id>`) — `src/game/worker_status.py`.
  - This module returns ~25 distinct human-readable strings (`Ready`, `Resting`, `Processing`, `No worker`, `Inactive`, `Output full`, `Storage full`, `Under construction`, `No wood/wheat/flour/water/chicken/bread/grain/grapes`, `Missing inputs`, `Moving`, `Sowing`, `Harvesting`, `Mining`, `On the way`, `Gathering`, `Depositing`, `At resource`, `At camp`, `Waiting target`, `No fields in radius`, `No ripe vineyards in range`, `Unknown`, etc.).
  - Decide a stable status-id scheme: keep the functions returning stable English ids OR introduce `status.<id>` keys and localize at the panel boundary. Prefer adding `status.<snake_id>` locale keys and a single `localized_status(s)` helper so panels render localized text while tests can still assert ids.
  - Map every returned string to a `status.*` key in both locales.
  - Update the status-helper test (find via `rg -l worker_status tests`); assert localized output for a few representative statuses in `en`+`ru`.
  - Verify: run the status test file; then `pytest -q`.
  - Acceptance: every status string has a locale key; tests assert consistent ids/output.
- [x] **T455**: Localize raw + processing building panels.
  - Files: `lumber_camp_panel.py`, `stone_mine_panel.py`, `iron_mine_panel.py`, `forester_hut_panel.py`, `well_panel.py`, `sawmill_panel.py`, `mill_panel.py`, `bakery_panel.py`, `winery_panel.py`.
  - Route their visible text — `Active`/`Inactive` toggles, `Demolish`, storage lines like `Grapes: {n} / {m}` / `Wine: {n} / {m}`, and any status text — through `ui.*`/`status.*`/`resource.*` keys. Resource/amount labels reuse `resource.<id>`.
  - Update the relevant panel tests (find via `rg -l "sawmill\|winery\|forester\|well_panel\|mill_panel\|bakery" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: no hard-coded visible English remains in these modules except ids/constants; tests pass.
- [x] **T456**: Localize Laboratory panels — `src/game/ui/laboratory_panel.py` + `laboratory_panel_research.py`.
  - Route `Scientists: {n} / {m}`, `Upgrade to Lv {n}`, slot labels `Empty`/`Sci`, `Active`/`Inactive`, `Active research`, and the research points line (`{current} / {required}`) through `ui.*`/`status.*`/`building.LABORATORY.*` keys.
  - Update `tests/test_laboratory_panel.py` and `tests/test_laboratory_labels.py`; add a `ru` smoke for the scientists line.
  - Verify: `pytest -q tests/test_laboratory_panel.py tests/test_laboratory_labels.py`; then `pytest -q`.
  - Acceptance: laboratory panel tests pass with localized text.
- [x] **T457**: Localize food/dining panels.
  - Files: `farm`-related panel, `vineyard_farm_panel.py`, `canteen_panel.py`, `restaurant_panel.py`, `chicken_farm_panel.py`, `cow_farm_panel.py`.
  - Route dining slot/status text, blocked reasons, and meal/resource labels through `status.*`/`resource.*`/`ui.*` keys. Meal labels reuse `resource.simple_meal` / `resource.elite_meal`.
  - Update the relevant panel tests (find via `rg -l "canteen\|restaurant\|chicken_farm\|cow_farm\|vineyard_farm" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: relevant panel tests pass; meal/resource labels come from locale paths.
- [x] **T458**: Localize school panel — `src/game/ui/school_panel.py`.
  - Route title, queue, Basic/Advanced tab labels, hire/cancel labels, worker labels (reuse `worker.<TYPE>`), and upgrade/demolish through `ui.*`/`worker.*` keys.
  - Update `tests/test_laboratory_menu.py` / school-panel tests (find via `rg -l school_panel tests`); assert Basic/Advanced tab labels in `en` and `ru`.
  - Verify: run the school-panel test file; then `pytest -q`.
  - Acceptance: school-panel tests pass for tab labels in both locales.
- [x] **T459**: Externalize research copy from `src/game/settings/research.json` (`research.<id>.*`).
  - Move each research's `name`, `description`, `effect_text` into `research.<id>.name/.desc/.effect` locale keys (ids include `1`, `carrier_speed_1`, `statue_excavation`, etc.). Keep ids, `resource_cost`, `required_points`, `tier`, `column`, `dependencies`, `image_key`, `worker_effects` in `research.json`.
  - Update `research_config.py`/loaders to read display copy from i18n by id; if the JSON still carries `name`/etc., have the loader prefer the locale and treat JSON text as a dev-only fallback (or remove it — record the choice).
  - Update research config tests (find via `rg -l research_config tests`) to validate the balance schema still loads; assert localized `name`/`effect` via i18n.
  - Verify: run research config/test files; `ruff check src tests`; then `pytest -q`.
  - Acceptance: balance schema still validates; UI copy resolves through i18n for every research id.
- [x] **T460**: Localize research screen + tooltip + start button.
  - Files: `research_screen.py` (`_TITLE = "Research"`, `Technology`, `Tier {n}`), `research_tile_tooltip.py` (`Cost`/`Points`/`Requires`/`Effect`/`Locked`, dependency names), `research_start_button.py` (`Start`).
  - Route all through `ui.research.*` keys; dependency and research names reuse `research.<id>.name` (T459).
  - Update tests (find via `rg -l "research_screen\|research_tile_tooltip\|research_start_button\|research_tile" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: research screen, tooltip, and start-button tests pass.
- [x] **T461**: Externalize statue stage names from `src/game/settings/buildings/statue.json` (`statue.stage.<n>`).
  - Move `stage_names` (`1:Excavation`, `2:Foundation`, `3:Pedestal`, `4:Statue`) to `statue.stage.1..4` locale keys. Keep `footprint`, `levels`, costs, `build_time_ms` in JSON.
  - Update `Statue.stage_name` (`src/game/buildings/statue.py`) to resolve via i18n, keeping the `Stage {n}` fallback.
  - Update `tests/test_statue.py`; assert English stage names and a `ru` stage-name smoke.
  - Verify: `pytest -q tests/test_statue.py`; then `pytest -q`.
  - Acceptance: statue stage names resolve through i18n in both locales.
- [x] **T462**: Localize lock reasons / requirement messages shown in UI.
  - Cover research eligibility reasons, laboratory requirement messages, active-research messages, and statue requirement messages (find sources via `rg -n "requires\|locked\|need\|requirement" src/game`).
  - Route through `ui.lock.*` / `status.*` keys, or keep stable reason ids localized at the UI boundary; record the approach.
  - Update the lock-reason tests (find via `rg -l "lock\|requirement\|eligib" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: lock/requirement messages compare localized strings or stable reason ids in tests.
- [x] **T463**: Enforce Russian locale completeness.
  - Add `tests/test_locale_completeness.py` that loads `en.json` and `ru.json` and asserts identical key sets, no missing values, and no empty/whitespace-only strings.
  - Fill any `ru` gaps the test surfaces.
  - Verify: `pytest -q tests/test_locale_completeness.py`; then `pytest -q`.
  - Acceptance: `en` and `ru` key sets match exactly; no empty values.
- [x] **T464**: Audit remaining player-facing literals in `src/game`.
  - Use `rg` to find remaining quoted human text in `src/game/ui`, `src/game/render.py`, `worker_status.py`, and runtime modules (e.g. `rg -n "\"[A-Z][a-z].*\"" src/game/ui`).
  - Migrate any genuine UI strings missed by earlier tasks; document a short allowlist (dev-only text like `dev_asset_reload.py`, ids/enums, log strings) in `localization_guide.md`.
  - Verify: `pytest -q`.
  - Acceptance: documented allowlist exists; no obvious UI strings remain outside locale files.
- [x] **T465**: Verify layout with Russian text.
  - Add headless render smoke checks under the `ru` locale (via T442 harness) for: bottom bar, building panel, worker panel, research screen, construction panel. Assert text surfaces fit within their target rects (no overflow beyond panel bounds).
  - Adjust widths/wrapping only where overflow is detected; do not restyle otherwise.
  - Verify: run the new layout test(s); then `pytest -q`.
  - Acceptance: no overflow in tested surfaces under `ru`.
- [x] **T466**: Update tests that still assume English literals.
  - Sweep the suite for assertions on raw English text that should be key-based or locale-controlled; convert them to assert via `t(key)` or under an explicit `en` harness block.
  - Verify: `pytest -q` (default `en` locale) passes fully.
  - Acceptance: full suite green; no brittle English-literal assertions remain for migrated modules.
- [x] **T467**: Finalize localization docs.
  - Complete `localization_guide.md`: locale folder, flat dotted-key naming, `{param}` syntax, fallback behavior, how to add a new language, and how tests switch locale (T442 harness).
  - Cross-link from `building_extension_guide.md`, `worker_extension_guide.md`, and `research_extension_guide.md` that new player-facing strings must go through `game.i18n` keys.
  - Verify: `python -c "import game.i18n"`; then `pytest -q`.
  - Acceptance: docs describe `src/game/settings/locales/`, key naming, and test expectations.
- [x] **T468**: Close Phase 29.
  - Run full verification (`pytest -q`; `ruff check src tests`).
  - Update Current Status, Decisions Log, Issues & Blockers, and archive Phase 29 task detail if the list grows too large.
