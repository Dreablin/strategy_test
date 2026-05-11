# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 25 - Vineyard Farm and Vineyards (**active**)
- **Next Task:** T330 - Vineyard harvest into farm storage
- **Last Completed:** T329 - Farmer vineyard movement
- **Total Progress:** 329 / 338 (Phase 25: 18 / 27 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 25 - Vineyard Farm and Vineyards

**Goal.** Add a `VINEYARD_FARM` staffed by the existing `FARMER`, plus separate 1-tile `VINEYARD` plots. Vineyards grow grapes automatically through timed stages. A farmer assigned to the Vineyard Farm harvests ripe nearby Vineyards into the farm's local storage, and carriers export grapes to Town Hall.

**Design notes.**

- Resource id: `grapes`.
- Town Hall warehouse stores `grapes`.
- Farm building type: `VINEYARD_FARM`.
- Plot building type: `VINEYARD`.
- Worker: reuse existing `FARMER`; do not add a new worker type.
- `VINEYARD_FARM` has 10 levels.
- `VINEYARD_FARM` local grape storage starts at 3 and increases by 1 each level.
- `VINEYARD_FARM` harvest radius is 15 cells.
- `VINEYARD` is a separate 1x1 buildable building/plot.
- Each `VINEYARD` construction costs 1 board.
- Once a `VINEYARD` is built, grapes grow automatically.
- Grapes have 4 maturation stages; each stage lasts 45 seconds.
- After a `VINEYARD` is harvested, it automatically restarts the growth cycle.
- All balance/configuration values belong in building JSON files:
  - `src/game/settings/buildings/vineyard_farm.json` for Vineyard Farm levels, storage, radius, worker effects, construction/upgrade costs/times, and any farm-specific timing.
  - `src/game/settings/buildings/vineyard.json` for Vineyard plot construction, 1x1 footprint expectations, maturation stage count, per-stage duration, and asset scale/anchor/offset metadata if this project stores those there for plot-style buildings.
- Asset folders and metadata should follow existing building/field conventions. If real assets are absent, add only minimal placeholders/fallback metadata needed for tests and runtime.
- Keep field/plot logic separate enough that Wheat Field behavior is not accidentally changed.
- Each implementation task must add/update its own focused tests, then end with full `pytest` and `ruff check src tests`.
- Do not create a task that only adds failing tests. Tests and implementation must land together in the same checked task.

### 25.1 Resource and Farm Foundation

- [x] **T312**: Add `grapes` as a complete warehouse resource. Update resource catalog/display label, Town Hall warehouse initialization/settings/UI, worker/population resource labels if needed, and focused tests proving `grapes` exists in Town Hall storage and renders in the warehouse panel. Run full `pytest` and `ruff check src tests`.
- [x] **T313**: Add only `src/game/settings/buildings/vineyard_farm.json`. Include `VINEYARD_FARM`, 10 levels, construction/upgrade costs/times, local grape storage capacity by level, harvest radius, and worker effects if matching current farm-building conventions. Add focused settings tests proving values are loaded from this JSON. Run full `pytest` and `ruff check src tests`.
- [x] **T314**: Add only the `VineyardFarm` building class shell. It should define `type_tag`, active flag if matching farm-like buildings, progress/storage fields needed later, `set_active` if applicable, `storage_capacity`, `grapes_amount`, `add_grapes_to_storage`, `take_grapes_from_storage`, and max level behavior via settings. Do not register it in menus/runtime yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T315**: Register `VINEYARD_FARM` for placement/construction only. Wire the class into placement maps and input construction selection so it can be placed and built, without adding menu visibility yet. Add focused placement/construction tests. Run full `pytest` and `ruff check src tests`.
- [x] **T316**: Add Vineyard Farm asset loading/fallback only. Add building folder mapping and placeholder/meta files only if real assets are absent; add focused asset tests proving construction and completed sprites resolve. Run full `pytest` and `ruff check src tests`.
- [x] **T317**: Add Vineyard Farm to the appropriate build menu only. Add the menu tile/click routing for `VINEYARD_FARM`; add focused bottom-bar/input tests. Run full `pytest` and `ruff check src tests`.
- [x] **T318**: Add Vineyard Farm display labels/descriptions only. Update building display names/descriptions and any placement labels that do not require a custom panel yet. Add focused label tests if existing patterns support them. Run full `pytest` and `ruff check src tests`.

### 25.2 Vineyard Plot Foundation

- [x] **T319**: Add only `src/game/settings/buildings/vineyard.json`. Include `VINEYARD`, construction cost of 1 board, build time, maturation stage count, per-stage duration, and asset scale/anchor/offset metadata according to existing asset metadata conventions. Add focused settings tests. Run full `pytest` and `ruff check src tests`.
- [x] **T320**: Add only the `Vineyard` 1x1 building/plot class shell. It should define `type_tag`, 1x1 footprint, construction support, growth state fields, and basic phase/stage accessors, but no runtime growth yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T321**: Register `VINEYARD` for placement/construction only. Wire the class into placement maps and input construction selection so plots can be placed and built, without adding menu visibility yet. Add focused placement/construction tests, including the 1-board construction requirement. Run full `pytest` and `ruff check src tests`.
- [x] **T322**: Add Vineyard plot asset loading/fallback only. Add folder mapping and placeholder/meta files only if real assets are absent; add focused tests proving each growth stage sprite resolves or falls back safely. Run full `pytest` and `ruff check src tests`.
- [x] **T323**: Add Vineyard plot to the appropriate build menu only. Add the menu tile/click routing for `VINEYARD`; add focused bottom-bar/input tests. Run full `pytest` and `ruff check src tests`.
- [x] **T324**: Add Vineyard display labels/descriptions only. Update building display names/descriptions and any placement labels that do not require custom runtime yet. Add focused label tests if existing patterns support them. Run full `pytest` and `ruff check src tests`.

### 25.3 Growth and Harvest Runtime

- [x] **T325**: Add Vineyard growth runtime only. Built Vineyards should advance through configured growth stages using `vineyard.json` timing and become ripe after the final stage; under-construction Vineyards should not grow. Add focused growth tests. Run full `pytest` and `ruff check src tests`.
- [x] **T326**: Add Vineyard harvest reset only. When a ripe Vineyard is marked harvested, it should restart growth from the first stage automatically. Add focused domain/runtime tests. Run full `pytest` and `ruff check src tests`.
- [x] **T327**: Add Vineyard Farm radius/target selection only. Implement selection of ripe `VINEYARD` plots within the configured Vineyard Farm radius, accounting for reserved/claimed plots so two farmers do not target the same plot. Add focused selection/reservation tests. Run full `pytest` and `ruff check src tests`.
- [x] **T328**: Add FARMER compatibility with `VINEYARD_FARM` only. Extend worker-building compatibility so existing `FARMER` can be assigned to both normal `FARM` and `VINEYARD_FARM`, without changing wheat farm behavior. Add focused assignment tests. Run full `pytest` and `ruff check src tests`.
- [x] **T329**: Add farmer movement to ripe Vineyard plots only. A Farmer assigned to Vineyard Farm should walk to a reachable ripe Vineyard in range and enter a harvesting state, without depositing grapes yet. Add focused movement/state tests. Run full `pytest` and `ruff check src tests`.
- [~] **T330**: Add Vineyard harvest completion into farm local storage only. Completing a Vineyard harvest should add grapes to Vineyard Farm local storage, reset the Vineyard growth cycle, release the plot reservation, and respect full farm storage. Add focused runtime tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T331**: Add Vineyard Farm worker rest/status integration only. After a grape harvest, the farmer should return/rest according to existing farm-style worker rhythm, and panel/status helpers should report Vineyard Farm states consistently. Add focused status/rest tests. Run full `pytest` and `ruff check src tests`.

### 25.4 Transport and UI

- [ ] **T332**: Add Vineyard Farm grape output export planning only. Carriers should export grapes from Vineyard Farm local storage to Town Hall, accounting for queued/in-flight grape exports and Town Hall capacity. Add demolition/invalid-task coverage for grapes if not already covered generically. Run full `pytest` and `ruff check src tests`.
- [ ] **T333**: Add Vineyard Farm panel shell only. Create/route a panel that shows title, worker status, upgrade, demolish, active toggle if the domain supports it, and close action, without custom storage/growth details yet. Add click/layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T334**: Add Vineyard Farm panel storage/status rows only. Show local grape storage and farmer status/production status in the panel without overlapping actions at level 10. Add draw/layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T335**: Add Vineyard plot panel or terrain-click behavior only. Decide based on existing field behavior: either make `VINEYARD` behave like terrain/no panel or show a minimal panel with growth stage. Add tests for the chosen click behavior. Run full `pytest` and `ruff check src tests`.

### 25.5 Documentation and Smoke Coverage

- [ ] **T336**: Update extension documentation only. Document Vineyard Farm/Vineyard patterns in `building_extension_guide.md` and worker guidance as needed: farm-with-plots, shared FARMER compatibility, plot growth JSON, asset metadata expectations, and carrier export expectations. Avoid hard-coding balance numbers in PRD-style docs except where the JSON is the source of truth. Run full `pytest` and `ruff check src tests`.
- [ ] **T337**: Add one focused integration test for Vineyard Farm + Vineyards. Cover constructing a Vineyard Farm and one Vineyard, growth to ripe, farmer harvest into farm storage, growth reset, and carrier export of grapes to Town Hall. Run full `pytest` and `ruff check src tests`.
- [ ] **T338**: Close Phase 25. Run final full `pytest` plus `ruff check src tests`; update Current Status, Last Completed, Total Progress, Decisions Log, and Notes; mark Phase 25 complete only when all tasks are `[x]`.

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
| 2026-05-10 | Phase 25 | Reuse `FARMER` for `VINEYARD_FARM`. | User requested the same worker as the normal farm; compatibility must support both farm types without changing wheat behavior. |
| 2026-05-10 | Phase 25 | Model `VINEYARD` as a separate 1x1 buildable plot. | User requested vineyards as separate one-cell buildings built near the farm. |
| 2026-05-10 | Phase 25 | Store Vineyard Farm and Vineyard constants in per-building JSON files. | Keeps balance/configuration near the building and avoids scattering constants through runtime code. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- **2026-05-10:** Phase 25 planned for Vineyard Farm and Vineyards. Tasks are split for ralph-loop execution: one resource, one settings file, one class shell, one menu/asset/UI/runtime/transport action per task where practical.
- **2026-05-10:** `FARMER` currently serves normal `FARM`; T328 should generalize compatibility carefully instead of duplicating one-off assignment paths.
- Keep old completed phase details in `progress_archive.md`; `progress.md` should stay focused on the current active phase to keep agent context small.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
