# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 23 - Well as staffed water producer
- **Next Task:** T284 - Remove obsolete direct-well symbols and tests in one complete cleanup slice
- **Last Completed:** T283 - Cover demolition and invalidation behavior for new water logistics
- **Total Progress:** 283 / 286 (Phase 23: 7 / 10 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 23 - Well as staffed water producer

**Goal.** Replace the old direct-well flow, where carriers reserve a well and draw water themselves, with a normal worker-operated producer building. A `WELL` has an assigned water worker, produces water into local storage, and carriers transport stored water from wells to water consumers. Water still must not be stored in Town Hall.

**Design notes.**

- Worker name: use `WATERMAN` unless the user asks for a different final name.
- `WELL` becomes a normal upgradable resource building:
  - 10 levels.
  - Construction and upgrades are configured in `src/game/settings/buildings/well.json`.
  - Local water storage capacity is configured in `well.json`: level 1 has 1 water, each later level adds 1.
  - Production timing and worker rest are configured in `well.json`.
- `WATERMAN` is hired through `SCHOOL`, appears in school/population/worker UI, and is assigned to `WELL`.
- Water production:
  - Requires an assigned `WATERMAN`.
  - Requires completed, active `WELL`.
  - Starts only when well local storage has free space.
  - Produces discrete `+1 water` into the well local storage.
  - Worker rests after each production cycle.
- Water logistics:
  - Water is never stored in Town Hall warehouse.
  - Water delivery tasks are generated from well local storage to any active water consumer exposing `water_amount`, `water_capacity`, and `add_water_in`.
  - Planning must account for queued and in-flight water deliveries so consumer capacity is not overpromised.
  - Source well selection should prefer nearest available stored water for the target where practical, but correctness and no overfill are more important than perfect routing.
- Old direct-well behavior must be removed, not layered under the new model:
  - No well `busy` flag.
  - No carrier-side water drawing timer.
  - No carrier reservation/release of wells.
  - No `WELL_DRAW_WATER_MS` transport special case.
  - No well panel status based on temporary carrier occupancy.
- Keep delivery queue logic capability-based. Do not hard-code water only to bakery/canteen/chicken farm.
- Every implementation task must end with full `pytest` and `ruff check src tests`.

### 23.1 Well domain, settings, and UI

- [x] **T277**: Convert `WELL` settings/domain to a normal local-storage building in one complete slice. Update `well.json` to 10 levels with construction/upgrade levels, storage capacity by level, production duration, and worker rest duration; refactor `Well` to remove `busy/reserve/release`; add water local storage helpers/progress fields/max level 10; update or rewrite focused well domain tests so they pass against the new model; run full `pytest` and `ruff check src tests`.
- [x] **T278**: Update Well UI/panel/status in one complete slice. Show local water storage, worker assignment/status, production/rest progress, active toggle if applicable, upgrade, and demolish; remove carrier-draw status/progress from `WellPanel`, `worker_status`, `workers.py`, and input panel calls; update panel/status tests so they pass; run full `pytest` and `ruff check src tests`.

### 23.2 WATERMAN hiring and assignment

- [x] **T279**: Add `WATERMAN` as a complete hireable worker slice. Add/adjust tests and implementation together for: school queue/hire UI, hire gates/settings, asset fallbacks/icons, population/worker labels, `WORKER_TO_BUILDING`, assignment to completed `WELL`, and full satiety on creation/hire; run full `pytest` and `ruff check src tests`.

### 23.3 Well production runtime

- [x] **T280**: Implement staffed well production as a complete runtime slice. Add/adjust tests and implementation together for: no worker means no water, inactive/under-construction well does not start new cycles, full storage blocks start, configured cycle produces `+1 water`, configured rest happens between cycles, worker remains inside/assigned correctly, and progress/status helpers match other staffed producers; run full `pytest` and `ruff check src tests`.

### 23.4 Water transport refactor

- [x] **T281**: Refactor water task planning as a complete slice. Replace direct free-well task generation with tasks from well local storage to active water consumers; account for queued/in-flight outbound water from wells and inbound water to consumers; prefer reasonable nearest-source routing where practical; add tests with multiple wells and multiple consumers proving later bakeries/canteens can receive water; run full `pytest` and `ruff check src tests`.
- [x] **T282**: Clean carrier transport water handling as a complete slice. Remove well reservation/release, carrier-side draw duration, carried-well-water special counting, and failed-pickup branches tied to `Well.busy`; make water behave like a local-storage resource except it has no Town Hall fallback; update carrier tests so they pass; run full `pytest` and `ruff check src tests`.
- [x] **T283**: Cover demolition and invalidation behavior for new water logistics in one complete slice. If a water source well or target consumer is demolished while queued/in-flight, carriers must not crash or trap resources; carried water may be dropped if no valid target exists; water must never be returned to Town Hall. Add/adjust tests and implementation together; run full `pytest` and `ruff check src tests`.

### 23.5 Old logic cleanup and documentation

- [ ] **T284**: Remove obsolete direct-well symbols and tests in one complete cleanup slice. Eliminate any remaining `water_worker_for_well`, `water_draw_progress_for_building`, direct draw panel wording, and old tests that only describe carrier-side drawing. (`WELL_DRAW_WATER_MS`, `Well.busy`, `reserve`/`release` removed in T282.) Replace them only with tests for the new producer/storage model where coverage would otherwise be lost. Run full `pytest` and `ruff check src tests`.
- [ ] **T285**: Update `PRD.md` for the new well model in one complete documentation slice. Document `WELL` as a normal staffed producer with local water storage, `WATERMAN` as its worker, water delivery from well local storage to consumers, and the rule that Town Hall never stores water. Remove old text about carriers reserving/drawing from wells. Run full `pytest` and `ruff check src tests`.
- [ ] **T286**: Add/update one end-to-end smoke test and close the phase. Cover well construction/setup, `WATERMAN` assignment, water production into local well storage, carrier delivery to at least two water consumers, no Town Hall water storage, and no starvation of the second consumer. Final gate: full `pytest` plus `ruff check src tests`; update Current Status and Notes; mark Phase 23 complete only when all tasks are `[x]`.

---

## Rules For Next Phase

- Keep exactly one active task marked `[~]` at a time.
- Start new work from the first unchecked `[ ]` task in the active phase.
- Each task must be independently finishable: add or update tests and implementation in the same task, and leave the full suite passing before marking `[x]`.
- Do not leave intentionally failing RED tests in a checked-in task. If a test must fail temporarily while working, finish the implementation before marking the task done.
- Mark `[x]` only after verification (`pytest`, and `ruff check src tests` when relevant).
- If blocked after repeated attempts, mark `[!]` and add a row in **Issues & Blockers**.

## Decisions Log

| Date | Task | Decision | Rationale |
|------|------|----------|-----------|
| 2026-05-08 | Phase 23 | Replace direct-well carrier drawing with staffed well production and local well storage. | The old model required special queue logic for wells and starved later water consumers. A normal producer model matches the rest of the economy and simplifies transport. |
| 2026-05-08 | Phase 23 | Use `WATERMAN` as the implementation worker type unless renamed later. | The user suggested a waterman-style worker; using one stable internal tag keeps tasks unblocked. |
| 2026-05-08 | Phase 23 | Water remains excluded from Town Hall storage. | Water should be produced locally at wells and delivered directly to consumers, preserving the existing non-warehouse water rule. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- **2026-05-08:** Phase 23 planning replaces the old direct-well flow. Start at T279. Tasks are vertical slices: each task updates tests and implementation together and must leave the full suite passing. The highest-risk cleanup areas are `transport_tasks.water_input_transport_tasks`, `worker_transport` water branches, `worker_status`, `WellPanel`, and tests that expect `Well.busy` / carrier-side drawing.
- **2026-05-08:** T283: `notify_demolished` drops any transport queue entries whose source or target is the demolished building; tests cover queued well removal, mid-route drops when the well or consumer is removed, and Town Hall never gains warehouse water.
- **2026-05-08:** Keep old completed phase details in `progress_archive.md`; `progress.md` should stay focused on the current active phase to keep agent context small.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
