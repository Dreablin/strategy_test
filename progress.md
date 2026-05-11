# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 26 - Wine, Winery, and Worker Tiers (**active**)
- **Next Task:** T340 - Add worker tier metadata
- **Last Completed:** T339 - Add `wine` as a complete Town Hall warehouse resource
- **Total Progress:** 339 / 360 (Phase 26: 1 / 22 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 26 - Wine, Winery, and Worker Tiers

**Goal.** Add `wine` as a Town Hall warehouse resource, add a `WINERY` processing building that turns grapes into wine, add worker tiers (`basic` / `advanced`), add school hire tabs by tier, and add an advanced `WINEMAKER` worker assigned to the Winery.

**Design notes.**

- Resource id: `wine`.
- Town Hall warehouse stores `wine`.
- Building type: `WINERY`.
- Worker type: `WINEMAKER`.
- Worker tier ids: `basic`, `advanced`.
- Existing worker types are `basic`.
- `WINEMAKER` is `advanced`.
- School hire UI must have `Basic` and `Advanced` tabs.
- A worker appears in the tab matching its configured tier.
- `WINERY` belongs in the Processing build menu.
- `WINERY` has 10 levels.
- `WINERY` local storage:
  - input: `grapes`
  - output: `wine`
  - level 1 capacity: 3 for each local resource
  - each level adds +1 capacity for both local resources
- Recipe: 3 grapes -> 1 wine.
- Production cycle: 60 seconds, then 10 seconds worker rest.
- Production runs only when:
  - the Winery is built,
  - the Winery is active,
  - a Winemaker is assigned/inside,
  - enough input grapes are in local storage,
  - output wine storage has free capacity.
- Carriers bring grapes into Winery local storage and export wine to Town Hall.
- Balance/configuration values for Winery belong in `src/game/settings/buildings/winery.json`.
- Worker tier data should be centralized with worker hiring metadata, not hard-coded in the School panel.
- Each implementation task must add/update its own focused tests, then end with full `pytest` and `ruff check src tests`.
- Do not create a task that only adds failing tests. Tests and implementation must land together in the same checked task.

### 26.1 Resource and Worker Tier Foundation

- [x] **T339**: Add `wine` as a complete Town Hall warehouse resource. Update resource catalog/display label, Town Hall warehouse initialization/settings, Town Hall storage UI, and focused tests proving `wine` exists in Town Hall storage and appears in the warehouse panel. Run full `pytest` and `ruff check src tests`.
- [ ] **T340**: Add worker tier metadata only. Introduce a centralized helper/data source that returns `basic` or `advanced` for a worker type, assign `basic` to every existing worker type, and add focused tests for known existing workers. Do not change the School UI yet. Run full `pytest` and `ruff check src tests`.
- [ ] **T341**: Add School panel tier filtering only. Make the School panel layout able to list hire buttons for a requested tier and prove the `basic` view contains existing basic workers. Do not add clickable tabs yet. Run full `pytest` and `ruff check src tests`.
- [ ] **T342**: Add clickable `Basic` / `Advanced` tabs to the School panel only. Add panel layout/click-action support and GameInput state/routing so tab selection persists while the panel is open. Add focused UI/input tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T343**: Add `WINEMAKER` as an advanced hireable worker only. Register the worker in hiring metadata with tier `advanced`, make it trainable from the School advanced tab, and add focused tests for tier, training queue, and hire selection. Do not assign it to any building yet. Run full `pytest` and `ruff check src tests`.
- [ ] **T344**: Add Winemaker display assets/labels only. Add worker dot/UI/hire icon fallback coverage and player-facing worker labels for `WINEMAKER`, without runtime assignment changes. Run full `pytest` and `ruff check src tests`.

### 26.2 Winery Building Foundation

- [ ] **T345**: Add only `src/game/settings/buildings/winery.json`. Include `WINERY`, footprint, 10 construction/upgrade levels, storage capacity by level, recipe, production cycle/rest timing, active default if used by processing buildings, and asset metadata. Add focused settings tests proving values are loaded from this JSON. Run full `pytest` and `ruff check src tests`.
- [ ] **T346**: Add only the `Winery` building class shell. Define `type_tag`, local grape input storage, local wine output storage, active flag, capacity helpers, add/take helpers, recipe/timing accessors, and progress helpers. Do not register placement or runtime yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T347**: Register `WINERY` for placement/construction only. Wire the class into placement maps and construction config usage so it can be placed and built, without menu visibility or runtime production. Add focused placement/construction tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T348**: Add Winery asset loading/fallback only. Add building folder mapping and placeholder/meta files only if real assets are absent; add focused asset tests proving construction and completed sprites resolve. Run full `pytest` and `ruff check src tests`.
- [ ] **T349**: Add Winery to the Processing build menu only. Add the menu tile/click routing for `WINERY` and focused bottom-bar/input tests that avoid brittle hard-coded per-button coordinate coverage where possible. Run full `pytest` and `ruff check src tests`.
- [ ] **T350**: Add Winery display labels/descriptions only. Update building display names/descriptions, population/worker building labels if needed, and construction panel display name. Add focused label tests. Run full `pytest` and `ruff check src tests`.

### 26.3 Transport and Runtime

- [ ] **T351**: Add Winery grape input transport planning only. Carriers should deliver grapes from valid grape sources into Winery local input storage, accounting for queued/in-flight deliveries and local input capacity. Add focused transport planning tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T352**: Add Winery wine output export planning only. Carriers should export wine from Winery local output storage to Town Hall, accounting for queued/in-flight exports and Town Hall capacity. Add focused transport tests, including stale/demolished task behavior if not covered generically. Run full `pytest` and `ruff check src tests`.
- [ ] **T353**: Add Winemaker-to-Winery compatibility and assignment only. Extend worker-building compatibility so `WINEMAKER` can be assigned to built `WINERY` buildings and no other worker is newly assigned to Winery. Add focused assignment tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T354**: Add Winery production runtime only. With an assigned Winemaker inside, active Winery, enough grapes, and output space, run the configured cycle, consume grapes, produce wine, then put the worker into configured rest. Add focused runtime tests for success and blocked cases. Run full `pytest` and `ruff check src tests`.
- [ ] **T355**: Add Winery production/worker status helpers only. Report no worker, inactive, no grapes, output full, processing, and resting states consistently with other processing buildings. Add focused status tests. Run full `pytest` and `ruff check src tests`.

### 26.4 Winery UI and Integration

- [ ] **T356**: Add Winery panel shell only. Route a custom panel for `WINERY` with title, worker status, close, upgrade, demolish, and active toggle actions. Do not add custom storage/progress rows yet. Add focused panel routing/click tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T357**: Add Winery panel storage and progress rows only. Show grape input storage, wine output storage, production status, blocked reason/progress bar, and ensure level 10 actions do not overlap. Add focused draw/layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T358**: Add one focused integration test for the wine chain. Cover grapes reaching a built Winery, Winemaker production of wine, and carrier export of wine to Town Hall. Keep the test bounded and deterministic. Run full `pytest` and `ruff check src tests`.

### 26.5 Documentation and Closure

- [ ] **T359**: Update extension documentation only. Document worker tiers, School tab rules, Winery processing/transport expectations, and where Winery constants live. Avoid duplicating balance numbers in PRD-style docs except to point to JSON as source of truth. Run full `pytest` and `ruff check src tests`.
- [ ] **T360**: Close Phase 26. Run final full `pytest` plus `ruff check src tests`; update Current Status, Last Completed, Total Progress, Decisions Log, and Notes; mark Phase 26 complete only when all tasks are `[x]`.

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

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- **2026-05-11:** Phase 26 planned for wine, Winery, worker tiers, School hire tabs, and Winemaker.
- Keep old completed phase details in `progress_archive.md`; `progress.md` should stay focused on the current active phase to keep agent context small.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
