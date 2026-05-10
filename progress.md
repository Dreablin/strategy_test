# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 24 - Cow Farm producer (**active**)
- **Next Task:** T303 - Add worker-building compatibility support for multi-building worker types only
- **Last Completed:** T302 - Cow Farm panel production status and progress bar
- **Total Progress:** 302 / 311 (Phase 24: 16 / 25 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 24 - Cow Farm producer

**Goal.** Add `COW_FARM`, a processing building staffed by the existing `ANIMAL_HERDER`. It consumes wheat and water from local input storage, produces two output resources (`beef` and `hide`) into local output storage, and carriers export those outputs to Town Hall warehouse.

**Design notes.**

- Building type: `COW_FARM`.
- Worker: reuse the existing `ANIMAL_HERDER`; do not create a new worker type.
- Player-facing name: Cow Farm.
- Internal output resource ids: `beef` and `hide`.
- Town Hall warehouse stores `beef` and `hide`.
- Water remains excluded from Town Hall warehouse; it is still delivered from well local storage to consumers.
- Cow Farm belongs in the processing build menu, alongside sawmill/mill/bakery/chicken farm.
- Cow Farm has 10 levels.
- Cow Farm settings must live in `src/game/settings/buildings/cow_farm.json`, not in hard-coded constants:
  - construction and upgrade costs/times,
  - local storage capacity per level,
  - production duration,
  - worker rest duration,
  - recipe inputs and outputs.
- Local storage capacity starts at 3 for every Cow Farm resource slot and increases by 1 every level. This applies to wheat, water, beef, and hide.
- One production cycle consumes 3 wheat and 3 water, then produces 1 beef and 1 hide.
- A cycle may start only when:
  - the building is completed and active,
  - an `ANIMAL_HERDER` is assigned and inside/working,
  - both inputs have enough resources for the recipe,
  - both output slots have enough free capacity for the recipe outputs.
- Between production cycles, the worker rests using the rest duration from `cow_farm.json`.
- Delivery planning must account for queued and in-flight resources when deciding whether Cow Farm needs wheat/water or has exportable beef/hide.
- Keep transport logic capability-based where practical. Do not add special-case code that only works for one named consumer if a generic local-storage producer/consumer path already exists.
- Each implementation task must add/update its own focused tests, then end with full `pytest` and `ruff check src tests`.
- Do not create a task that only adds failing tests. Tests and implementation must land together in the same checked task.

### 24.1 Resources and domain foundation

- [x] **T287**: Add `beef` as a complete warehouse resource. Update resource catalog/display label, Town Hall warehouse initialization/settings/UI, worker/population resource labels if needed, and focused tests proving `beef` exists in Town Hall storage and renders in the warehouse panel. Run full `pytest` and `ruff check src tests`.
- [x] **T288**: Add `hide` as a complete warehouse resource. Update resource catalog/display label, Town Hall warehouse initialization/settings/UI, worker/population resource labels if needed, and focused tests proving `hide` exists in Town Hall storage and renders in the warehouse panel. Run full `pytest` and `ruff check src tests`.
- [x] **T289**: Add only `src/game/settings/buildings/cow_farm.json`. Include `COW_FARM` building type, 10 construction/upgrade levels, storage capacity by level, production duration, worker rest duration, and recipe input/output values. Add focused settings tests proving values are loaded from this JSON. Run full `pytest` and `ruff check src tests`.
- [x] **T290**: Add only the `CowFarm` building class shell in `src/game/buildings/cow_farm.py`. It should define `type_tag`, slots, active flag, progress fields, `set_active`, `storage_capacity`, and `max_level` behavior via settings, but no registration/menu/runtime yet. Add focused domain tests. Run full `pytest` and `ruff check src tests`.
- [x] **T291**: Add Cow Farm wheat input storage helpers only. Implement `wheat_amount`, `wheat_capacity`, `add_wheat_in`, `take_wheat_in`, and overflow/underflow tests. Run full `pytest` and `ruff check src tests`.
- [x] **T292**: Add Cow Farm water input storage helpers only. Implement `water_amount`, `water_capacity`, `add_water_in`, `take_water_in`, and overflow/underflow tests. Run full `pytest` and `ruff check src tests`.
- [x] **T293**: Add Cow Farm beef output storage helpers only. Implement `beef_amount`, `beef_capacity`, `add_beef_out`, `take_beef_out`, and overflow/underflow tests. Run full `pytest` and `ruff check src tests`.
- [x] **T294**: Add Cow Farm hide output storage helpers only. Implement `hide_amount`, `hide_capacity`, `add_hide_out`, `take_hide_out`, and overflow/underflow tests. Run full `pytest` and `ruff check src tests`.
- [x] **T295**: Add Cow Farm recipe/progress helper methods only. Read recipe amounts and production timing from `cow_farm.json`; add helpers for checking recipe input availability, output free space, `processing_progress`, and `progress_state`. Add focused tests. Run full `pytest` and `ruff check src tests`.

### 24.2 Build menu, assets, and panel

- [x] **T296**: Register `COW_FARM` for placement/construction only. Wire the building class into placement maps and input construction selection so a Cow Farm can be placed and built, without adding menu visibility yet. Add focused placement/construction tests. Run full `pytest` and `ruff check src tests`.
- [x] **T297**: Add Cow Farm asset loading/fallback only. Add the building folder mapping and placeholder/meta files only if real assets are absent; add focused asset tests proving construction and completed sprites resolve. Run full `pytest` and `ruff check src tests`.
- [x] **T298**: Add Cow Farm to the processing build menu only. Add the processing-menu tile and click routing for `COW_FARM`; add focused bottom-bar/input tests. Run full `pytest` and `ruff check src tests`.
- [x] **T299**: Add Cow Farm display labels/descriptions only. Update building display names/descriptions and any placement/panel labels that do not require a custom panel yet. Add focused label tests if existing patterns support them. Run full `pytest` and `ruff check src tests`.
- [x] **T300**: Add Cow Farm panel shell only. Create `CowFarmPanel`, route it from input, and show title/worker status/upgrade/demolish/active toggle using existing base layout, without custom storage/progress details yet. Add click/layout tests. Run full `pytest` and `ruff check src tests`.
- [x] **T301**: Add Cow Farm panel storage rows only. Show wheat, water, beef, and hide local storage values in the panel. Add draw/layout tests proving rows render without overlapping actions. Run full `pytest` and `ruff check src tests`.
- [x] **T302**: Add Cow Farm panel production status/progress only. Show blocked reason and processing progress bar using Cow Farm helpers. Add tests for running, missing inputs, full outputs, inactive, and no-worker display states. Run full `pytest` and `ruff check src tests`.

### 24.3 Worker assignment and production runtime

- [~] **T303**: Add worker-building compatibility support for multi-building worker types only. Refactor assignment compatibility so `ANIMAL_HERDER` can target both `CHICKEN_FARM` and `COW_FARM`, while existing worker assignments remain unchanged. Add focused assignment/reassignment tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T304**: Add Cow Farm processor runtime only. Add a processor spec/update path for `COW_FARM` using JSON duration/rest and recipe; verify one cycle consumes wheat/water and produces beef/hide, with active/no-worker/under-construction/full-output gates. Add focused runtime tests. Run full `pytest` and `ruff check src tests`.
- [ ] **T305**: Add Cow Farm production status integration only. Make worker/building status helpers report Cow Farm states consistently with other processors. Add focused status tests. Run full `pytest` and `ruff check src tests`.

### 24.4 Transport integration

- [ ] **T306**: Add Cow Farm wheat input delivery planning only. Carriers should deliver wheat to Cow Farm when planned inbound wheat plus stored wheat is below capacity. Add tests for no overfill with queued/in-flight wheat. Run full `pytest` and `ruff check src tests`.
- [ ] **T307**: Add Cow Farm water input delivery planning only. Carriers should deliver water from well local storage to Cow Farm when planned inbound water plus stored water is below capacity. Verify existing Bakery/Canteen/Chicken Farm water delivery still works. Run full `pytest` and `ruff check src tests`.
- [ ] **T308**: Add Cow Farm beef output export planning only. Carriers should export beef from Cow Farm local output storage to Town Hall, accounting for queued/in-flight beef exports. Add demolition/invalid-task coverage for beef if not already covered generically. Run full `pytest` and `ruff check src tests`.
- [ ] **T309**: Add Cow Farm hide output export planning only. Carriers should export hide from Cow Farm local output storage to Town Hall, accounting for queued/in-flight hide exports. Add demolition/invalid-task coverage for hide if not already covered generically. Run full `pytest` and `ruff check src tests`.

### 24.5 Documentation and smoke coverage

- [ ] **T310**: Update documentation only. Update `PRD.md`, `building_extension_guide.md`, and any worker guide text needed for shared worker compatibility and multi-output processors. Avoid hard-coding numeric balance values in PRD. Run full `pytest` and `ruff check src tests`.
- [ ] **T311**: Add one Phase 24 end-to-end smoke test and close the phase. Cover Cow Farm construction/setup, `ANIMAL_HERDER` assignment, wheat + water delivery, production of beef + hide, export to Town Hall, and no Town Hall water storage. Final gate: full `pytest` plus `ruff check src tests`; update Current Status and Notes; mark Phase 24 complete only when all tasks are `[x]`.

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
| 2026-05-10 | Phase 24 | Reuse `ANIMAL_HERDER` for Cow Farm. | User requested the same worker as Chicken Farm; assignment logic should support one worker type serving multiple compatible animal buildings. |
| 2026-05-10 | Phase 24 | Use internal resource ids `beef` and `hide`. | They are concise, stable ids for player-facing beef and hide. |
| 2026-05-10 | Phase 24 | Keep Cow Farm recipe, timing, rest, and storage capacity in `cow_farm.json`. | Building-specific balance belongs in per-building JSON so agents do not need to edit large global settings for each building. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- **2026-05-10:** Phase 24 planned for Cow Farm. Tasks are ordered so no task is only a failing-test step; each task must include implementation plus its own tests.
- **2026-05-10:** Phase 24 tasks were split into smaller ralph-loop slices after review: one resource, one storage slot, one UI part, or one transport flow per task where practical.
- **2026-05-10:** `ANIMAL_HERDER` currently serves `CHICKEN_FARM`; T303 should generalize compatibility carefully instead of duplicating one-off assignment paths.
- Keep old completed phase details in `progress_archive.md`; `progress.md` should stay focused on the current active phase to keep agent context small.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
