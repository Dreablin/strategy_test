# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 28 - Laboratory and Research (**in progress**)
- **Next Task:** T406 - Add Laboratory upgrade/construction pause behavior for Scientists only
- **Last Completed:** T405 - Add Laboratory demolition cleanup for Scientists only
- **Total Progress:** 405 / 438 (Phase 28: 19 / 52 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

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
- [ ] **T406**: Add Laboratory upgrade/construction pause behavior for Scientists only. While the Laboratory is under construction/upgrading, Scientists should not contribute or appear as active workers; after completion, reassignment may fill available slots. Add focused upgrade/construction lifecycle tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T407**: Add Laboratory panel Scientist slot display only. Show Scientist slots and assigned/empty state in the Laboratory panel without adding active research display yet. Add focused panel layout/draw tests. Run full `pytest` and `ruff check src tests`.

### 28.4 Top Bar and Research Screen Shell

- [ ] **T408**: Add top-bar Research button visibility only. Show the "Research" button only when a completed Laboratory exists; hide it while no Laboratory exists or the Laboratory is under construction. Do not open a screen yet. Add focused top-bar tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T409**: Add Research screen open/close shell only. Clicking the top-bar Research button opens a full-screen modal overlay; close/Esc returns to the game. Do not draw research rows or tiles yet. Add focused input/modal tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T410**: Add four-row research screen layout only. Draw four equal-height tier rows and a left static Technology column area using configured row positions. Do not add research tiles, start buttons, or eligibility yet. Add focused layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T411**: Add research tile rendering only. Render configured research tiles at their configured tier/column with image and title. Do not add dim/full-color completion state or clickable start buttons yet. Add focused draw/layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T412**: Add research tile completion visual state only. Completed research tiles render full-color; not-started and in-progress tiles render dimmed/partially transparent. Do not add start buttons yet. Add focused rendering tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T413**: Add per-tile Start button rendering only. Render a button directly below each tile with the required spacing, visually enabled/disabled from a supplied eligibility flag. Do not handle clicks yet. Add focused layout tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T414**: Add research requirement tooltip only. Hovering a research tile should show a compact tooltip with configured cost, required points, dependencies, and lock reason text supplied by eligibility logic. Do not start research from the tooltip. Add focused UI tests. Run full `pytest` and `ruff check src tests`.

### 28.5 Research Eligibility and Start Flow

- [ ] **T415**: Add base research eligibility rules only. Implement pure/domain checks for: completed research cannot start, active research blocks all starts, and a completed Laboratory must exist. Do not add level-tier gates or dependency gates yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T416**: Add Laboratory level tier gates only. Extend eligibility so Laboratory level unlocks research tiers according to Laboratory settings. Do not add dependency gates yet. Add focused eligibility tests for levels 1, 3, 6, and 9. Run full `pytest` and `ruff check src tests`.
- [ ] **T417**: Add research dependency gates only. Extend eligibility so configured dependency ids must be completed before a research can start. Do not add UI button wiring yet. Add focused dependency tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T418**: Add research config validity checks to eligibility only. Ensure researches with invalid/empty cost shape or non-positive point requirements are treated as non-startable with a clear lock reason, even if the loader normally prevents them. Add focused defensive tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T419**: Wire Research screen button enabled state to eligibility only. Disabled buttons should be grey/transparent and non-startable; enabled buttons should look active. Do not mutate active research on click yet. Add focused UI tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T420**: Add domain start-active-research behavior only. Starting an eligible research should set the active research id and reject starting any other research while one is active. Do not create dynamic input storage yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T421**: Add dynamic input storage creation on research start only. When research starts, initialize Laboratory dynamic input storage exactly for that research's cost map with zero delivered amounts. Do not wire UI clicks yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T422**: Wire Start button click to domain start only. Clicking an eligible Start button should call the domain start flow and leave the selected research uncancellable. Do not add carrier delivery yet. Add focused input/domain tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T423**: Add Laboratory dynamic input storage display only. Laboratory panel should show the active research image and one row per required input resource with real delivered amount/capacity. Do not add carrier delivery or point progress yet. Add focused panel tests. Run full `pytest` and `ruff check src tests`.

### 28.6 Research Resource Logistics

- [ ] **T424**: Add Laboratory input-demand planning only. For the active research, carriers should create tasks from Town Hall to Laboratory for required warehouse resources, accounting for already delivered, queued, and in-flight amounts. Do not deliver resources yet. Add focused transport planning tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T425**: Add carrier delivery into Laboratory dynamic storage only. Carriers should deliver research input resources into the Laboratory's active research storage and reject overfill/irrelevant resources. Add focused delivery tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T426**: Add invalidation handling for active research deliveries only. If the Laboratory is demolished while research inputs are queued or in-flight, normal carried resources should return to Town Hall using existing invalid-delivery semantics, and the active research should not trap carriers. Add focused edge-case tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T427**: Add "resources delivered" gate only. Research point production must not start until every required resource amount for the active research has been delivered. Add focused domain/runtime tests with no Scientist timing behavior beyond stubs. Run full `pytest` and `ruff check src tests`.

### 28.7 Research Point Runtime and Completion

- [ ] **T428**: Add single-Scientist research point production only. With one assigned Scientist inside a completed Laboratory and all resources delivered, accumulate points over elapsed game time using configured points-per-second. Do not handle multiple Scientists yet. Add focused runtime tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T429**: Add multi-Scientist linear scaling only. Accumulated points should scale linearly with the number of active Scientists inside the Laboratory, up to Laboratory slot capacity. Add focused runtime tests for two and max-capacity Scientists. Run full `pytest` and `ruff check src tests`.
- [ ] **T430**: Exclude absent/dining Scientists from research speed only. Scientists who are dining, walking to eat, returning from dining, idle, unassigned, or otherwise not active inside the Laboratory should not contribute points. Add focused runtime tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T431**: Add research completion only. When accumulated points reach the configured requirement, mark the research complete, clear active research/dynamic input storage/progress, and allow the next eligible research to start. Add focused completion tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T432**: Add Technology chain unlock behavior only. Completing Technology `1` should allow eligible tier-2 researches when Laboratory level permits, and so on through Technology `4`. Add focused eligibility tests for dependency and Laboratory-level gates. Run full `pytest` and `ruff check src tests`.

### 28.8 Research Progress UI Integration

- [ ] **T433**: Add Laboratory active research progress UI only. Laboratory panel should show active research image, progress bar, and numeric points like `350 / 10000` once the research has started. Add focused panel tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T434**: Add Research screen active progress state only. The full-screen Research menu should visually mark the currently active research as in-progress. Do not change completed/not-started state from earlier rendering. Add focused UI tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T435**: Add top-bar Research button state refresh only. The button should appear/disappear correctly after Laboratory construction completion, demolition, and rebuild, without requiring restart. Add focused integration tests. Run full `pytest` and `ruff check src tests`.

### 28.9 Integration and Documentation

- [ ] **T436**: Add one bounded end-to-end Laboratory/Research integration test only. Cover building a completed Laboratory, hiring/assigning a Scientist, opening the research screen, starting Technology `1`, delivering its resources, accumulating points, completing it, and unlocking the next Technology according to gates. Do not update documentation or close the phase in this task. Run full `pytest` and `ruff check src tests`.
- [ ] **T437**: Update Laboratory/Research documentation only. Update PRD and extension documentation so future agents know where to add research definitions, Laboratory settings, Scientist staffing rules, research UI behavior, and transport integration rules. Do not change runtime code or tests unless documentation references need path/name corrections. Run full `pytest` and `ruff check src tests` if code changed; otherwise run `ruff check src tests`.
- [ ] **T438**: Close Phase 28 progress only. After every Phase 28 task is `[x]`, update Current Status, Last Completed, Total Progress, Decisions Log, Notes, and archive/phase-completion wording as needed. Do not add feature code in this task. Run final full `pytest` plus `ruff check src tests`; mark Phase 28 complete only when all checks pass.

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
| 2026-05-27 | Phase 28 | Research definitions live in a dedicated JSON file. | Research layout, dependencies, costs, points, and assets must be data-driven rather than hard-coded in UI/runtime. |
| 2026-05-27 | Phase 28 | Laboratory uses multi-staff Scientist slots. | Laboratory differs from normal one-worker buildings; slot capacity comes from Laboratory settings and research speed scales with active Scientists. |
| 2026-05-27 | Phase 28 | This phase implements framework and Technology researches only. | Concrete non-Technology research effects were not specified; adding gameplay effects should be planned after their ids/effects are known. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| 2026-05-27 | Phase 28 | Exact Laboratory construction/upgrade costs and exact research costs/point requirements are balance values. | Use JSON-configured values; adjust when final balance is provided. |
| 2026-05-27 | Phase 28 | Concrete non-Technology research list and gameplay effects are not specified. | Out of scope for Phase 28 except for schema/framework support. |

## Notes

- Keep old completed phase details in `progress_archive.md`; `progress.md` should stay focused on the current active phase to keep agent context small.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Worker effects rules: **`worker_effects_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
