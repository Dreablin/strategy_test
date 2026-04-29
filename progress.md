# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 19 — Construction System (queued)
- **Next Task:** T191 — wire `complete_construction` into `WorkerManager.update()`
- **Last Completed:** T190 — add `complete_construction()` for level apply + builder release + resting worker resume
- **Total Progress:** 190 / 209 (Phase 19: 6 / 25 tasks done)

> **Archive:** Phases **T01–T160** are recorded in **`progress_archive.md`**. Do **not** re-run completed tasks. Long-form phase write-ups were removed from this file to keep Ralph context small; use the archive for history.

---

## Hot-fix index (historic)

| ID | Summary |
|----|---------|
| HF12-A | LumberCamp Upgrade vs Demolish hit-test — fixed in `lumber_camp_panel.py`. |
| HF13–HF14 | Stable tests: `world_seed` pins; ring-20 stone vs map-centre clearing. |
| HF15–HF16 | Tree grove counts / priority TH-ring groves (`world.py`). |
| HF17 | Hiring only from School; spawn at hiring school; Town Hall hire UI removed. |

---

## Phase 15 — Housing, School queue, population HUD (active Ralph queue)

**Goal.** Schools train workers in a **7-slot FIFO queue** (**30 s** per trainee, **no resource cost**), gated by **housing**: **Town Hall** `8 + 2×(L−1)` + each **House** `2 + 2×(L−1)`. **Top bar** shows **current (max cap)** with a **population icon**; the **four resource + income strip is removed** from the HUD.

**PRD:** **F-HOUSING**, **F-SCHOOL-Q**, **F-HOUSE**, **F-POP-UI**, **F-UI-TOP** (Phase 15), **F-WORK-02**.

### 15.1 Domain — housing & caps

- [x] **T161**: Failing tests + module (e.g. `src/game/housing.py`): `housing_town_hall(L)`, `housing_house(L)`, `max_population(registry, worker_manager_or_count)`; pure functions, no hidden globals.
- [x] **T162**: Enforce **housing gate** on enqueue / train completion: training **cannot** start or finish into `current_population > max_population` (disabled UI + safe no-op; tests for both).

### 15.2 School — training queue core

- [x] **T163**: Failing tests for per-`SCHOOL` queue: **7** slots, fill **leftmost empty**, **only slot 0** trains, **30_000 ms** per unit, **shift left** on complete; multiple schools **independent**.
- [x] **T164**: Wire queue to game time (`now_ms`): completion spawns worker using **existing school spawn** rules; then `reassign_all`; **remove food / hire costs** from school training (config + `WorkerManager` / panel).

### 15.3 UI — School row + Top bar

- [x] **T165**: `SchoolPanel`: **7** squares in a row — worker icon + **yellow** progress bar at bottom of active training cell; enqueue buttons respect cap + full queue.
- [x] **T166**: Replace top-bar **resource** strip with **population** display: icon + `current (max N)` (see PRD **F-UI-TOP**); headless layout / surface test.

### 15.4 House building

- [x] **T167**: Failing tests: `HOUSE` type, **2×2**, levels **1..10**, housing contribution per level, registry placement rules.
- [x] **T168**: Implement `House`, costs/unlocks in `config.py` + `game_settings.json`, **Social** menu entry, assets folder + procedural sprite path.
- [x] **T169**: **Demolish vs over-cap** policy with tests (choose one consistent behaviour per **F-HOUSE-03** — e.g. block demolish if it would drop max below current pop).

### 15.5 Assets

- [x] **T170**: `assets/ui/population/default.png` (or agreed name) + `assets.py` disk-first load and procedural fallback (**F-POP-UI**).

### 15.6 Regression & phase close

- [x] **T171**: Sweep tests and smoke paths: remove expectations for **instant** school hire, **food** cost on hire, **top-bar resources**; keep `world_seed` pins where procedural terrain matters.
- [x] **T172**: New headless smoke: queue two trainees, housing blocks third, second `SCHOOL` has separate queue (minimal scenario).
- [x] **T173**: Full `pytest -q` + `ruff check src tests`; update **Decisions Log**; mark all Phase 15 `[x]`; emit `<promise>ALL_TASKS_COMPLETE</promise>`; create **empty** `.cursor/ralph/done`.

---

## Phase 16 — Carrier transport queue foundation

**Goal.** Introduce baseline transport execution for `CARRIER`: producers drop resources into local storage, carriers pull transport jobs from a queue, pick up from source building, and deliver to target building (currently Town Hall warehouse).

**PRD:** F-WORK (carrier), F-BLD (warehouse behavior baseline).

- [x] **T174**: Implement worker-level transport queue and carrier runtime loop: `source -> target` tasks, pickup from `StorageMixin`, delivery to Town Hall warehouse, and compatibility fallback to legacy direct deposit when no carriers exist.

---

## Phase 17 — Remove abstract spend-cost economy

**Goal.** Remove legacy “wallet” economy for building placement, upgrades, and hiring. These actions become free; UI no longer shows build/upgrade/hire prices tied to non-physical resource counters.

**PRD:** cleanup task for current carrier/warehouse direction.

- [x] **T175**: Remove build/upgrade/hire spend checks and cost labels; keep physical storage/warehouse counters only; update regression tests and run full suite.
- [x] **T176**: Remove leftover compatibility layer (`game.buildings.costs`, `ResourceManager.has/try_spend`) and rewrite tests to stop using wallet-spend helpers.

---

## Phase 18 — Remove ResourceManager globally

**Goal.** Fully remove `ResourceManager` and all global resource counters. Single source of truth for physical resources is warehouse/local storages.

- [x] **T177**: Runtime migration — route producer deposits and carrier deliveries to `TownHall.warehouse` only; remove fallback paths and direct global `resources.add(...)` writes.
- [x] **T178**: API migration — remove `ResourceManager` dependencies from `main/input/ui panels/placement/registry/workers` signatures and wiring.
- [x] **T179**: Test migration — replace `ResourceManager` fixtures/usages with warehouse-centric setup and assertions; delete `tests/test_resources.py`.
- [x] **T180**: Cleanup + verification — delete `src/game/resources.py`, scrub PRD references, run full `pytest -q` + `ruff check src tests`.
- [x] **T181**: Food/Wheat normalization cleanup — remove legacy alias flow (`food` ↔ `wheat`) from assets/panels/warehouse APIs; converge on one canonical key and update labels/tests.
- [x] **T182**: Remove per-cycle remnants — delete dead `per_cycle` / `sync_resources_per_cycle` logic and related tests/docs that describe legacy cycle totals.
- [x] **T183**: Remove runtime fallback branches that still read from global resources (e.g., TownHallPanel `warehouse_amount` fallback path) once warehouse is the only source of truth.
- [x] **T184**: Config/domain final cleanup — remove `economy.initial_resources` from settings/config (or relocate to warehouse bootstrap config), and update all tests/docs expecting `INITIAL_RESOURCES`.

---

## Phase 19 — Construction System

**Goal.** Buildings no longer appear instantly. When placed, a **construction site** appears (unfinished asset). It has a local **resource request** (from `game_settings.json`). **Carriers** deliver required materials with **highest priority**. Once all resources are delivered a **Builder** enters the site and spends a configured **build duration** there; a **progress bar** is shown in the building panel. On completion the site becomes a fully functional building and the builder exits. **Upgrades** follow the same flow: the building turns into a "level N+1 under construction" site, production stops, existing worker idles inside, resources + builder needed again. Produced resources are now routed to construction sites first, warehouse second.

**PRD refs:** F-BLD extension, F-WORK (BUILDER / CARRIER), new F-CONSTRUCT (to be added to PRD after Phase 19).

### 19.1 Settings — construction costs & build times

- [x] **T185**: Add `construction` section to `game_settings.json` and `config.py`. Structure: `construction.<BUILDING_TYPE>.levels.<N>` with `cost: {resource: amount, ...}` and `build_time_ms: int` for each building type + each level (1 = initial build, 2..10 = upgrade). Load into `CONSTRUCTION_REQUIREMENTS: dict[str, dict[int, ConstructionSpec]]` in `config.py`. Add reasonable defaults for all current building types (LUMBER_CAMP, STONE_MINE, IRON_MINE, FARM, FORESTER_HUT, SCHOOL, HOUSE). Write failing tests in `tests/test_construction_config.py` that assert structure, all types covered, costs non-negative, build_time_ms > 0. Then implement so tests pass.

### 19.2 Domain — ConstructionSite state on Building

- [x] **T186**: Add `ConstructionSite` dataclass in a new module `src/game/construction.py`. Fields: `required_resources: dict[str, int]`, `delivered_resources: dict[str, int]`, `build_time_ms: int`, `build_started_ms: int | None`, `builder: Worker | None (reference)`, `target_level: int`. Pure methods: `is_fully_supplied() -> bool`, `is_building() -> bool`, `build_progress(now_ms) -> float` (0.0–1.0), `is_complete(now_ms) -> bool`, `remaining_resources() -> dict[str, int]`, `deliver_resource(resource, amount)`. Write failing tests in `tests/test_construction.py`. Then implement.

- [x] **T187**: Add optional `construction_site: ConstructionSite | None` slot to `Building` base class. When `construction_site is not None`, the building is considered **under construction** and non-functional. Add property `is_under_construction -> bool`. Ensure all existing `Building.__init__` subclasses remain compatible (default `None`). Write tests that existing buildings still work unchanged; new building with a `construction_site` set returns `is_under_construction == True`.

### 19.3 Registry — place as construction site

- [x] **T188**: Modify `BuildingRegistry.place()` to look up `CONSTRUCTION_REQUIREMENTS` for the building type at level 1. If an entry exists, set `building.construction_site = ConstructionSite(...)` on the newly placed instance. Existing behaviour (place → functional) must still work for types without construction config (currently TOWN_HALL has no construction cost). Write tests: place a LUMBER_CAMP → verify `is_under_construction`, verify `construction_site.required_resources` matches config. Place TOWN_HALL → verify NOT under construction.

- [x] **T189**: Modify `BuildingRegistry.upgrade_building()` to initiate a construction site for the **next level** instead of instantly incrementing level. Store `target_level = building.level + 1` in the `ConstructionSite`. The building keeps its current level until construction completes; `is_under_construction` becomes True. If the building has a worker assigned (e.g. LUMBERJACK), that worker transitions to state `"resting"` inside the building (idle but not unassigned). Return `True` to indicate upgrade process started. Write tests: upgrade a level-1 building → verify `is_under_construction`, `target_level == 2`, worker state if assigned.

### 19.4 Construction completion logic

- [x] **T190**: Add `complete_construction(building, now_ms)` function in `construction.py`. When `construction_site.is_complete(now_ms)`: set `building.level = target_level`, clear `construction_site = None`, release the builder (set idle state, unassign from site), if there was a resting worker inside the building → restore to `"working"` state. Write tests for level-1 initial build completion (building becomes functional) and level-N upgrade completion (level increments, worker resumes). Ensure building bonuses are refreshed after level change.

- [ ] **T191**: Wire `complete_construction` into `WorkerManager.update()` loop: each frame, iterate buildings with `is_under_construction and construction_site.is_building()`, check `is_complete(now_ms)`, call completion. After any completion, call `reassign_all()`. Write test: building + builder inside → advance time past build_time_ms → building is no longer under construction, builder is idle.

### 19.5 Builder worker — construction state machine

- [ ] **T192**: Add BUILDER updater to `WorkerManager._updaters` dispatch (currently BUILDER has no updater). States: `"idle"` → look for a building with `is_under_construction and construction_site.is_fully_supplied() and construction_site.builder is None` → walk to approach tile → `"entering_site"` (park inside) → set `construction_site.builder = worker`, `construction_site.build_started_ms = now_ms` → state `"building"` → waits inside until `is_complete(now_ms)` (completion handled by T191). Write tests: idle builder + fully supplied site → builder walks to site and starts building.

- [ ] **T193**: Handle builder leaving after construction complete: when `complete_construction` clears the builder reference, the builder should move to an approach tile of the completed building, then become `idle`. If no approach tile is available, stand at building center. Write tests: after completion, builder is idle and positioned at approach tile.

- [ ] **T194**: Handle edge case: builder is walking to a construction site that gets demolished mid-way. Builder should abort, become idle at current tile. Add to `notify_demolished` logic. Similarly, if the builder is inside and the building is demolished, builder becomes idle. Write tests.

### 19.6 Transport priority — construction site delivery

- [ ] **T195**: Add `construction_transport_tasks(registry) -> list[TransportTask]` function in `construction.py` (or `workers.py`). Scan all buildings with `is_under_construction`, compute `remaining_resources()`, generate transport tasks from **Town Hall warehouse** to the construction site. These tasks should be distinguishable as **high priority**. Add `priority: int` field to `TransportTask` (default 0, construction = 10). Write tests.

- [ ] **T196**: Modify `WorkerManager._next_transport_task()` to sort by priority descending before picking the next task. High-priority construction tasks are served before normal warehouse-delivery tasks. Write tests: when both normal and construction tasks exist, carriers pick construction tasks first.

- [ ] **T197**: Generate construction transport tasks automatically: when a building becomes `is_under_construction` (place or upgrade), enqueue the needed resources as high-priority transport tasks sourced from Town Hall warehouse. When a resource is delivered (carrier unloads at construction site), call `construction_site.deliver_resource(resource, 1)`. Write tests: place building → transport tasks created → carrier delivers → `delivered_resources` incremented → `is_fully_supplied()` eventually becomes True.

- [ ] **T198**: Handle "resource not available" scenario. Modify carrier logic: when a carrier picks up a construction transport task but the Town Hall warehouse has no stock of the required resource, skip it (don't discard — leave in queue) and try the next task. The task stays in the queue until the resource becomes available. Write tests: construction needs `stone: 5`, warehouse has 0 → carrier does not pick up stone task → stone is produced → carrier picks up.

### 19.7 Smart resource routing — produce → need → warehouse

- [ ] **T199**: Refactor the resource deposit path in `_update_gatherer` (depositing state). Currently, after depositing into local building storage, a transport task is created targeting Town Hall. New logic: **first** check if any construction site needs this resource type (`remaining_resources()[resource] > 0`). If yes, create a high-priority transport task to that construction site instead of Town Hall. If no site needs the resource, fall back to Town Hall delivery as before. Write tests: construction site needs wood → lumberjack deposits wood → transport task targets the construction site, not Town Hall.

- [ ] **T200**: Handle the case where a construction site is satisfied mid-delivery. If a carrier is en route to a construction site with a resource it no longer needs (another carrier already delivered the last unit), the carrier should deliver to Town Hall warehouse instead. Adjust carrier unloading logic to check `remaining_resources()` before calling `deliver_resource`. If site doesn't need it, redirect to warehouse. Write tests.

### 19.8 UI — Construction panel

- [ ] **T201**: Create `src/game/ui/construction_panel.py` with `ConstructionPanel` class. When a building with `is_under_construction` is clicked, show a **construction-specific panel** instead of the normal building panel. Panel contents: building name + "Under Construction" (or "Upgrading to Lv N"), resource requirements list (icon + delivered/required for each resource), builder status ("Waiting for resources" / "Waiting for builder" / "Building..."), progress bar (yellow, 0–100%) during active building, Close [×] button, **no** Upgrade/Demolish buttons while under construction. Write headless layout/draw tests.

- [ ] **T202**: Wire `ConstructionPanel` into `GameInput.draw_panel()` and `_handle_map_left_click()`. When `self._panel.is_under_construction`, delegate to `ConstructionPanel` instead of the normal panel dispatcher. The construction panel only supports `close` click action. Write tests: click on under-construction building → construction panel shown; click close → panel closes.

### 19.9 Assets & rendering for construction sites

- [ ] **T203**: Add `building_sprite_construction(b_type, target_level)` to `assets.py`. Disk-first load from `assets/buildings/<folder>/construction.png` (or `construction_<level>.png`); procedural fallback: semi-transparent version of the building sprite with a scaffold overlay (wooden beams). Write tests: function returns a surface; fallback is used when no disk asset.

- [ ] **T204**: Modify `Renderer.draw_buildings()` to check `building.is_under_construction`. If true, use `building_sprite_construction(type_tag, construction_site.target_level)` instead of `building_sprite(type_tag, level)`. Write tests: under-construction building renders with construction sprite, completed building renders normally.

### 19.10 Upgrade flow — production halt & worker rest

- [ ] **T205**: When a building enters upgrade-construction (`T189`), stop all production for that building: if building has `active` attribute, set `active = False` (will be restored on completion). The assigned worker (if any) should be parked inside the building with state `"resting"` — they stay assigned but do not gather/produce. On construction completion, restore `active = True` and set worker back to `"working"` state. Write tests: lumberjack is gathering → upgrade starts → lumberjack stops, state = "resting" → construction completes → lumberjack resumes.

- [ ] **T206**: Ensure `worker_status_for_building` and `production_status_for_building` report construction states correctly. During construction: worker status = "resting" (if worker present) or "empty"; production status = "Under construction". Add the `"resting"` worker state handling in the status methods. Write tests.

### 19.11 Regression, integration & phase close

- [ ] **T207**: Regression sweep: ensure all existing tests still pass with the new `construction_site` slot on `Building`. Buildings that skip construction (TOWN_HALL) must continue to work instantly. Existing placement/demolish/upgrade tests must not break. Fix any failures. Run full `pytest -q` + `ruff check src tests`.

- [ ] **T208**: Integration smoke test (`tests/test_smoke_phase19.py`): end-to-end scenario — place a LUMBER_CAMP (enters construction) → carrier delivers wood+stone from warehouse → builder walks to site → building completes → lumberjack auto-assigns → chops tree → deposits → upgrade lumber camp to level 2 → construction starts → carrier delivers → builder builds → upgrade completes → lumberjack resumes. Minimal time-advancing headless test.

- [ ] **T209**: Full `pytest -q` + `ruff check src tests`; update Decisions Log; mark all Phase 19 tasks `[x]`; emit `<promise>ALL_TASKS_COMPLETE</promise>`; create `.cursor/ralph/done`.

---

## Decisions Log

| Date | Task | Decision | Rationale |
|------|------|----------|-----------|
| 2026-04-27 | HF12-A | Hit-resolve LumberCamp panel against `extra_bottom_px=72` only (drop legacy fallback). | Legacy fallback returned `"demolish"` for clicks on the visible Upgrade button (28 px overlap). |
| 2026-04-27 | T96+ | Movement & gather speed bonuses are additive (per PRD F-CHAR-02), not multiplicative. | Easier to reason about cumulative debuffs; user explicitly requested additive stacking. |
| 2026-04-27 | T103 | Storage capacity formula `3 + 2 × (L − 1)` = 3, 5, 7 … 21 over levels 1..10. | User specified +2 per level on top of base 3. |
| 2026-04-27 | T111 | Stone generation obsolete count in old PRD line; see `world.py` / F-STONE for **6** clusters + ring-20. | Spec evolved; trust code + F-STONE block. |
| 2026-04-27 | T132 | BFS uses 4 neighbours only (N/E/S/W), no diagonal moves and no corner-cut handling. | User asked workers to walk only horizontally/vertically. |
| 2026-04-27 | T160 | Runtime growth scheduler source-of-truth is `WorkerManager.update` → `world.update_tree_growth(now_ms)`. | Ensures planted-tree maturation advances in gameplay and tests without extra wiring. |
| 2026-04-28 | HF17 | Worker hire spawn is anchored to the hiring `School` building; Town Hall hire UI removed. | All hiring centralized at School. |
| 2026-04-28 | Prep | Phase 15 queued: school **7×30s** queue, **housing** from TH+House, **HUD** population only (see PRD). | User request; Ralph tasks T161–T173. |
| 2026-04-28 | T162 | Housing cap gate enforced in School hire flow: UI disabled via `can_hire`, backend `hire` returns no-op when over cap. | Prevents over-cap worker creation at both interaction and domain layers. |
| 2026-04-28 | T163 | Queue API contract tests define 7-slot FIFO, 30s front-only training, left-shift on completion, independent per-school timers. | Locks expected behavior before implementation (T164). |
| 2026-04-28 | T164 | School clicks enqueue free training; `WorkerManager.update` advances per-school queues and spawns completed trainees before `reassign_all`. | Aligns runtime with Phase 15 queue semantics and removes food-cost dependency from School training flow. |
| 2026-04-28 | T165 | School panel now renders a 7-slot queue row with worker icons and active yellow progress bar; enqueue controls disable when queue is full/cap blocked. | Matches F-SCHOOL-Q visual contract and keeps button affordances in sync with queue/housing gates. |
| 2026-04-28 | T166 | Top bar now renders population icon + `current (max N)` using worker count and housing cap instead of resource strip. | Aligns HUD with Phase 15 population-first UX and adds headless layout/draw coverage. |
| 2026-04-28 | T167 | Added RED coverage for `House` class contract, housing contribution, and registry placement/overlap semantics. | Defines expected behavior before implementing `House` and Social wiring in T168. |
| 2026-04-28 | T168 | Added `House` building class, wired placement/bottom-bar Social entry/config gates, and created `assets/buildings/house/` disk path with procedural fallback. | Completes House core integration so placement, costs, and rendering paths are available for Phase 15 follow-ups. |
| 2026-04-28 | T169 | Chosen policy: block `HOUSE` demolition if removal would make `current_population > max_population`; allow otherwise. | Prevents creating invalid over-cap state while keeping demolition deterministic and testable. |
| 2026-04-28 | T170 | Added disk asset `assets/ui/population/default.png` and `assets.population_icon()` disk-first loader with procedural fallback; TopBar now uses asset helper. | Establishes swap-friendly icon pipeline while keeping UI resilient when asset files are missing. |
| 2026-04-28 | T171 | Added explicit regression coverage that School enqueue is non-instant and free (no food spend), while top-bar tests remain population-focused. | Guards Phase-15 behavior changes against accidental rollback to legacy instant/food-based hiring and resource-strip HUD assumptions. |
| 2026-04-28 | T172 | Added Phase-15 headless smoke with two-school queue progression and housing-cap blocked enqueue at cap. | Provides minimal end-to-end guard that queue timing, school independence, and cap gating work together. |
| 2026-04-28 | T173 | Final verification gate passed: full `pytest -q` and `ruff check src tests` are green; completion marker file created. | Closes Phase 15 with reproducible validation and deterministic Ralph loop termination flag. |
| 2026-04-28 | T174 | Added generic `TransportTask` queue in `WorkerManager`; `CARRIER` now walks to source, takes 1 unit, walks to target, and delivers to Town Hall warehouse + spendable resource pool. | Establishes extensible building-to-building transport pipeline while preserving old no-carrier economy path. |
| 2026-04-28 | T175 | Removed wallet cost gates for placement/upgrade/hiring and switched UI labels to “Free”; deleted cost tables from settings/config and updated tests. | Aligns economy with physical-storage direction and removes legacy abstract spend model. |
| 2026-04-28 | T176 | Deleted legacy `game.buildings.costs`, removed `ResourceManager.has/try_spend`, and migrated tests to explicit add/get semantics. | Completes cost-economy removal so no dead compatibility APIs remain in runtime code. |
| 2026-04-28 | T177 | Removed runtime `resources.add(...)` writes from gather and carrier delivery; producer output now enters local storage then warehouse via transport pipeline only. | Establishes Town Hall warehouse as the sole runtime accumulation sink before API-level ResourceManager removal in T178+. |
| 2026-04-28 | T178 | Removed `ResourceManager` imports/type-coupling from runtime wiring (`main/input/ui panels/placement/registry/workers`) while keeping compatibility arguments where still used by tests. | Decouples runtime API surfaces from global resource manager before the dedicated test-side migration in T179. |
| 2026-04-28 | T179 | Removed `tests/test_resources.py` and migrated multiple runtime-smoke/regression tests from wallet assertions (`resources.get`/`per_cycle`) to warehouse-centric checks (`TownHall.warehouse_amount`, delivered counters, storage paths). | Aligns test expectations with warehouse-as-source-of-truth before deleting `resources.py` in T180. |
| 2026-04-28 | T180 | Removed `src/game/resources.py`; `WorkerManager` no longer takes `ResourceManager`; `main` wires `WorkerManager(registry, now_ms_fn=...)`; fixed `test_workers` `now_ms_fn` call to use `registry=None` keyword. **`PRD.md` not edited** (contract read-only). | Completes module deletion and verification; PRD text may still mention legacy resources until a future docs pass outside Ralph contract edits. |
| 2026-04-28 | T181 | Canonical crop key is **`wheat`**: dropped TownHall `food`→`wheat` normalization; `assets._resource_colors` uses `wheat`; `economy.initial_resources` and defaults use `wheat` instead of `food`; UI copy and tests updated. **`PRD.md` not edited** (still lists legacy `food` in F-RES). | Single warehouse/settings vocabulary; PRD resource names are stale until allowed to be revised. |
| 2026-04-28 | T182 | Deleted `BuildingRegistry.sync_resources_per_cycle` (no-op), its `upgrade_building` tail call, and `GameInput._sync_assignments` hook; production/building tests renamed to assert staffing, upgrades, and no passive ticks without the stub API. **`PRD.md` not edited** (still mentions `.per_cycle` in type sketch). | Removes dead cycle-sync surface; PRD type lines remain historical. |
| 2026-04-28 | T183 | Removed legacy **`resources`** parameter/`GameInput` slot and `PlacementController` storage; all building panels + `BottomBar` + `upgrade_building` no longer accept a wallet; warehouse display was already `TownHall.warehouse_amount` only. | Eliminates dead global-resource API surface; `INITIAL_RESOURCES` in config remains for T184. |
| 2026-04-28 | T184 | Replaced `economy.initial_resources` / `INITIAL_RESOURCES` with **`warehouse_bootstrap.town_hall`** in JSON + `TOWN_HALL_STARTING_WAREHOUSE`; **`bootstrap_starting_warehouse`** seeds the placed Town Hall in **`main` only** so tests keep empty warehouses by default. | Aligns config with warehouse source-of-truth; gameplay start matches prior 200/200 wheat/wood. **`PRD.md` not edited**. |
| 2026-04-29 | T185 | Added `ConstructionSpec` + `CONSTRUCTION_REQUIREMENTS` parsing in `config.py`; introduced `construction.<TYPE>.levels.<N>.{cost,build_time_ms}` for all Phase-19 building types with levels 1..10 in `game_settings.json`; added `tests/test_construction_config.py`. | Locks construction settings contract before runtime integration tasks (T186+). |
| 2026-04-29 | T186 | Added `src/game/construction.py` with `ConstructionSite` dataclass and pure methods (`is_fully_supplied`, `is_building`, `build_progress`, `is_complete`, `remaining_resources`, `deliver_resource`); added `tests/test_construction.py`. | Establishes core construction state model before wiring into `Building`/registry/workers in T187+. |
| 2026-04-29 | T187 | Added `construction_site` to `Building.__slots__` with default `None` and new `is_under_construction` property; extended `tests/test_buildings.py` to verify default compatibility and explicit construction-site state. | Prepares all building subclasses for construction flow without breaking existing behavior. |
| 2026-04-29 | T188 | `BuildingRegistry.place()` now attaches level-1 `ConstructionSite` from `CONSTRUCTION_REQUIREMENTS` for configured building types; Town Hall remains instant (no construction config). Added registry tests for both paths. | Enables place-as-construction behavior needed before upgrade/runtime construction flow. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Extended history and completed phase checklists: **`progress_archive.md`**.
- After Phase 13, orthogonal paths are longer than diagonal-allowing BFS; **F-PATH** / **F-WORK-07** in PRD match **4-dir** `find_path_bfs`.
