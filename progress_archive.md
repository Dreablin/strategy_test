# Progress Archive — Phases 1–12 and 28

This archive holds the original detailed task lists for completed phases. The
live task tracker (`progress.md`) stays minimal once a phase is closed; full
task text for Phase 28 lives below.

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
