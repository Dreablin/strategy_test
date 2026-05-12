# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 27 - Restaurant and Advanced Dining (**active**)
- **Next Task:** T380 - Add dining fallback behavior tests
- **Last Completed:** T379 - Add Restaurant dining runtime integration
- **Total Progress:** 379 / 386 (Phase 27: 19 / 26 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 27 - Restaurant and Advanced Dining

**Goal.** Add a `RESTAURANT` social building that mirrors the Canteen dining loop for advanced workers, uses the same `COOK` worker type, produces local-only `elite_meal`, and feeds only advanced-tier workers. Keep Canteen dining for basic-tier workers.

**Design notes.**

- Building type: `RESTAURANT`.
- Menu category: Social.
- Worker type: `COOK`.
- `COOK` can work in both `CANTEEN` and `RESTAURANT`.
- Dining eligibility is based on worker tier, not workplace:
  - `basic` workers reserve/eat `simple_meal` in `CANTEEN`.
  - `advanced` workers reserve/eat `elite_meal` in `RESTAURANT`.
- `COOK` remains `basic` unless a separate task changes worker tier metadata later; a basic cook assigned to a Restaurant still eats in a Canteen.
- Local-only resource id: `elite_meal`.
- `elite_meal` is not stored in the Town Hall warehouse and must not be exported there.
- Restaurant local storage:
  - inputs: `bread`, `wine`, `beef`
  - output: `elite_meal`
  - values and per-level capacity live in `src/game/settings/buildings/restaurant.json`.
- Restaurant production:
  - runs only when built, active, and assigned Cook is inside;
  - consumes configured inputs and produces configured local output;
  - cycle/rest values live in `restaurant.json`.
- Restaurant dining:
  - uses the same slot reservation, meal reservation, FIFO eating order, walking-to-building, progress bar, slot release, and return-to-work behavior as Canteen.
  - workers only leave for dining when both a suitable meal and a diner slot can be reserved immediately.
  - a reserved diner appears in the building panel immediately; while physically walking to the dining building, their tile icon is dimmed/partially transparent.
  - because a meal is reserved before the worker starts walking, newly implemented Restaurant dining must not rely on workers sitting inside and waiting for food.
  - if no suitable building/slot/meal is available, the worker continues normal work.
  - after eating, workers must walk back toward their assigned workplace before resuming work; they must not visually snap home at meal completion.
- Balance/configuration values for Restaurant belong in `src/game/settings/buildings/restaurant.json`, not in Python constants, except tiny ids/labels where the codebase already uses ids.
- Each implementation task must add/update focused tests for its change, then end with full `pytest` and `ruff check src tests`.
- Do not create a task that only adds failing tests. Tests and implementation must land together in the same checked task.

### 27.1 Dining Foundation Refactor

- [x] **T361**: Add `elite_meal` as a local-only resource label only. Update the resource catalog/display label and asset/resource icon fallback color so UI code can render it, but do not add Town Hall storage or any production/transport behavior. Add focused tests proving `elite_meal` has a display label and is not a Town Hall warehouse resource. Run full `pytest` and `ruff check src tests`.
- [x] **T362**: Generalize diner slot reservation helpers without changing behavior. Rename or extend the current Canteen-only reservation helpers so they can operate on any dining building with `_diner_occupants`, `_reserved_meal_workers`, `diner_slot_capacity()`, `meal_resource_key()`, and local storage helpers. Keep Canteen behavior identical. Add focused tests around Canteen reservations. Run full `pytest` and `ruff check src tests`.
- [x] **T363**: Generalize dining runtime without adding Restaurant. Update `worker_dining.py` so walking, FIFO reserved-meal consumption, eating progress, slot release, and return-to-work use generic dining-building helpers while preserving Canteen behavior and public worker states. Add focused tests proving existing Canteen dining only starts after a slot+meal reservation, still walks to the dining building, eats, releases slots, and starts a real return path instead of snapping home at meal completion. Run full `pytest` and `ruff check src tests`.
- [x] **T364**: Add dining tier metadata for existing Canteen only. Give dining buildings a configured eligible worker tier and make Canteen explicitly serve `basic` workers, with no Restaurant yet. Add focused selection tests proving basic workers can reserve Canteen meals and advanced workers do not use Canteen meals. Run full `pytest` and `ruff check src tests`.

### 27.2 Restaurant Building Foundation

- [x] **T365**: Add only `src/game/settings/buildings/restaurant.json`. Include `RESTAURANT`, footprint, 10 construction/upgrade levels, storage capacity by level, diner slot capacity by level, recipe, production cycle/rest timing, active default if used, worker effects, and asset metadata. Add focused settings tests proving values are loaded from this JSON. Run full `pytest` and `ruff check src tests`.
- [x] **T366**: Add only the `Restaurant` building class shell. Define `type_tag`, active flag, local storage resources, local storage helpers, diner slot helpers, meal resource key, dining tier, recipe helpers, timing/progress helpers, and upgrade capacity behavior. Do not register placement, menus, transport, production, or UI yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T367**: Register `RESTAURANT` for placement/construction only. Wire the class into placement maps and construction config usage so it can be placed and built, without menu visibility, production, dining selection, or transport. Add focused placement/construction tests. Run full `pytest` and `ruff check src tests`.
- [x] **T368**: Add Restaurant asset loading/fallback only. Add building folder mapping and placeholder/meta files only if real assets are absent; add focused asset tests proving construction and completed sprites resolve. Run full `pytest` and `ruff check src tests`.
- [x] **T369**: Add Restaurant to the Social build menu only. Add the Social menu tile/click routing for `RESTAURANT` and focused bottom-bar/input tests that avoid brittle hard-coded per-button coordinate coverage where possible. Run full `pytest` and `ruff check src tests`.
- [x] **T370**: Add Restaurant display labels/descriptions only. Update building display names/descriptions, population/worker building labels if needed, and construction panel display name. Add focused label tests. Run full `pytest` and `ruff check src tests`.

### 27.3 Restaurant Production and Transport

- [x] **T371**: Add Cook-to-Restaurant compatibility and assignment only. Allow `COOK` to be assigned to built `RESTAURANT` buildings while preserving existing Canteen assignment behavior. Add focused assignment tests for Cook with both buildings. Run full `pytest` and `ruff check src tests`.
- [x] **T372**: Add Restaurant bread input transport only. Carriers should deliver `bread` from valid sources into Restaurant local input storage, accounting for queued/in-flight deliveries and local capacity. Add focused transport planning and delivery tests for `bread`. Run full `pytest` and `ruff check src tests`.
- [x] **T373**: Add Restaurant wine input transport only. Carriers should deliver `wine` from valid sources into Restaurant local input storage, accounting for queued/in-flight deliveries and local capacity. Add focused transport planning and delivery tests for `wine`. Run full `pytest` and `ruff check src tests`.
- [x] **T374**: Add Restaurant beef input transport only. Carriers should deliver `beef` from valid sources into Restaurant local input storage, accounting for queued/in-flight deliveries and local capacity. Add focused transport planning and delivery tests for `beef`. Run full `pytest` and `ruff check src tests`.
- [x] **T375**: Add Restaurant production runtime only. With an assigned Cook inside, active Restaurant, enough configured inputs, and output space, run the configured cycle, consume inputs, produce `elite_meal`, then put the Cook into configured rest. Add focused runtime tests for success and blocked cases. Run full `pytest` and `ruff check src tests`.
- [x] **T376**: Add Restaurant production/worker status helpers only. Report no worker, inactive, missing input, output full, processing, and resting states consistently with other processing/social producer buildings. Add focused status tests. Run full `pytest` and `ruff check src tests`.
- [x] **T377**: Prevent local-only `elite_meal` export only. Ensure transport/task planning never exports `elite_meal` to Town Hall and that direct enqueue safeguards treat it as local-only like `simple_meal`. Add focused negative transport tests. Run full `pytest` and `ruff check src tests`.

### 27.4 Restaurant Dining Selection

- [x] **T378**: Add Restaurant to dining selection for advanced workers only. Hungry advanced workers should reserve the nearest reachable Restaurant only when both an available slot and an unreserved `elite_meal` exist; basic workers should continue using Canteen only. Add focused selection tests with both building types present, including one test proving no worker leaves work when Restaurant slots are free but no `elite_meal` is available. Run full `pytest` and `ruff check src tests`.
- [x] **T379**: Add Restaurant dining runtime integration only. WorkerManager should assign reserved meals and update dining runtime for Restaurant occupants using the generic dining loop. Add focused tests proving an advanced worker appears reserved while walking, walks to Restaurant, eats `elite_meal`, releases the slot, and starts walking back to work instead of snapping home. Run full `pytest` and `ruff check src tests`.
- [ ] **T380**: Add dining fallback behavior tests only with implementation if needed. Prove that a hungry advanced worker keeps working when no Restaurant meal/slot is reservable, and a hungry basic worker keeps working when only Restaurant meals exist. Also prove that reserved meals prevent over-assignment when multiple hungry workers compete for fewer available meals. If the existing code already satisfies this after earlier tasks, this task only adds passing focused tests. Run full `pytest` and `ruff check src tests`.

### 27.5 Restaurant UI and Integration

- [ ] **T381**: Add Restaurant panel shell only. Route a custom panel for `RESTAURANT` with title, worker status, close, upgrade, demolish, and active toggle actions. Do not add custom storage/progress/diner rows yet. Add focused panel routing/click tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T382**: Add Restaurant panel storage and production progress rows only. Show bread, wine, beef, `elite_meal`, production status, blocked reason, and production progress without overlapping buttons. Add focused draw/layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T383**: Add Restaurant panel diner tiles only. Show reserved/arriving/eating advanced diners using the same visual semantics as Canteen: dimmed/partially transparent icon while walking, normal icon while waiting at the restaurant or eating, and progress bar while eating. Add focused panel tests for all three visual states. Run full `pytest` and `ruff check src tests`.
- [ ] **T384**: Add one focused Restaurant production integration test. Cover inputs reaching a built Restaurant, Cook production of `elite_meal`, and no Town Hall export of the local-only output. Keep the test bounded and deterministic. Run full `pytest` and `ruff check src tests`.
- [ ] **T385**: Add one focused advanced dining integration test. Cover an advanced worker becoming hungry, reserving a Restaurant meal, walking there, eating, restoring satiety, releasing the slot, and returning to work without teleporting. Keep the test bounded and deterministic. Run full `pytest` and `ruff check src tests`.

### 27.6 Documentation and Closure

- [ ] **T386**: Update extension documentation and close Phase 27. Document generic dining-building rules, Basic/Canteen vs Advanced/Restaurant selection, local-only meal resources, Restaurant config location, and Cook compatibility expectations. Run final full `pytest` plus `ruff check src tests`; update Current Status, Last Completed, Total Progress, Decisions Log, and Notes; mark Phase 27 complete only when all tasks are `[x]`.

---

## Rules For Next Phase

- Keep exactly one active task marked `[~]` at a time.
- Start new work from the `[~]` task if present; otherwise start from the first unchecked `[ ]` task in the active phase.
- Each task must be independently finishable: add or update tests and implementation in the same task, and leave the full suite passing before marking `[x]`.
- Do not leave intentionally failing RED tests in a checked-in task. If a test must fail temporarily while working, finish the implementation before marking the task done.
- Mark `[x]` only after verification (`pytest`, and `ruff check src tests` when relevant).
- After marking a task `[x]`, move `[~]` to the next unchecked task and update Current Status.
- If blocked after repeated attempts, mark `[!]` and add a row in **Issues & Blockers**.

## Decisions Log

| Date | Task | Decision | Rationale |
|------|------|----------|-----------|
| 2026-05-11 | Phase 26 | Add worker tiers as centralized hiring metadata. | School UI must derive tabs from worker type data so future workers are not hard-coded into UI branches. |
| 2026-05-11 | Phase 26 | Put existing workers in `basic` and `WINEMAKER` in `advanced`. | User requested all existing workers as Basic and the new Winemaker as Advanced. |
| 2026-05-11 | Phase 26 | Store Winery constants in `winery.json`. | Keeps building balance/configuration with the building and matches current building-extension guidance. |
| 2026-05-11 | Phase 27 | Dining destination is selected by worker tier, not by assigned workplace. | A worker's food tier should stay predictable and independent from the building they are currently working in. |
| 2026-05-11 | Phase 27 | Treat `elite_meal` as local-only like `simple_meal`. | Restaurant meals should stay in Restaurant local storage and never become Town Hall warehouse goods. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- **2026-05-11:** Phase 27 planned for Restaurant, advanced dining, `elite_meal`, and generic dining-building reuse.
- Keep old completed phase details in `progress_archive.md`; `progress.md` should stay focused on the current active phase to keep agent context small.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
