# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 21 — Wheat fields + farmer field cycle
- **Next Task:** Phase 21 complete
- **Last Completed:** T245 — Final verification gate
- **Total Progress:** 245 / 245 (Phase 19: 25 / 25 done; Phase 20: 11 / 11 done; Phase 21: 25 / 25 done)

> **Archive:** Full history and completed phases are in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 21 — Wheat fields + farmer field cycle

**Goal.** Add new buildable **FIELD** (1x1, built by Builder, no resource delivery), wheat growth on fields (4 phases, 45s each), farmer work loop (harvest priority, then sow), farm local storage integration, and carrier transport through the existing shared transport queue.

**PRD refs (to add/align):** F-BLD/F-CONSTRUCT extensions for FIELD, F-WORK farmer cycle, crop growth lifecycle, transport queue integration.

### 21.1 Domain scaffold — field entity and wheat phases

- [x] **T221**: Add failing tests for new `FIELD` building type: footprint **1x1**, placeable from **Resource/Production** menu, cannot be upgraded (or level fixed at 1), and walkability semantics: field tile is always walkable for all workers. Include placement/registry/pathfinding assertions.
- [x] **T222**: Implement `Field` domain model/building class + registration wiring (`config`, placement mapping, bottom bar entry under production/resource group). Keep construction resource cost empty (`{}`) and construction time `10_000 ms`.
- [x] **T223**: Add wheat lifecycle domain model in a dedicated module (or field module): states `PHASE_1..PHASE_4` plus `EMPTY` (ready-to-sow). Add pure helpers for transitions and timestamps. Write RED tests for state progression and reset-after-harvest.

### 21.2 Construction flow — builder-on-tile build for FIELD

- [x] **T224**: Add failing tests for FIELD-specific construction behavior: builder path target is the field tile itself (not approach tile), builder stands on tile, build progress runs for `10_000 ms`, then construction completes into built field.
- [x] **T225**: Implement FIELD construction specialization in builder/construction runtime while keeping generic construction behavior unchanged for other buildings. Ensure no carrier resource delivery tasks are generated for FIELD construction sites.
- [x] **T226**: Add rendering/UI support for FIELD construction progress bar under builder while building (on-map world progress bar). Include headless render test that verifies bar appears only during FIELD build.

### 21.3 Wheat growth runtime

- [x] **T227**: Add failing tests for wheat autonomous growth timing on built fields: `PHASE_1 -> PHASE_2 -> PHASE_3 -> PHASE_4`, each step every `45_000 ms`, growth pauses only if field is not sown.
- [x] **T228**: Implement runtime growth updater (world/worker manager tick path): deterministic timestamp-based progression using existing `now_ms` flow; no per-frame floating accumulation drift.
- [x] **T229**: Add tests + implementation for harvest reset: when farmer harvests `PHASE_4`, field becomes `EMPTY` immediately and can be selected for sowing in the same/next farmer cycle.

### 21.4 Farmer behavior cycle (Farm worker AI)

- [x] **T230**: Add RED tests for farmer assignment lifecycle: after hire farmer enters farm, rests, then starts field work cycles from farm home base.
- [x] **T231**: Add RED tests for farmer target selection priority within radius **10** (Chebyshev) from assigned farm:  
  1) pick ripe field (`PHASE_4`) first;  
  2) if none, pick empty field (`EMPTY`) for sowing;  
  3) if neither exists, stay/rest and retry later.
- [x] **T232**: Implement farmer navigation + action loop for **harvest** action: move to target field tile, perform `5_000 ms` action with progress bar, then carry wheat back to farm local storage.
- [x] **T233**: Implement farmer navigation + action loop for **sow** action: move to empty field tile, perform `5_000 ms` action with progress bar, set field to `PHASE_1`, return to farm.
- [x] **T234**: Integrate standard post-action rest cycle (same rest semantics as other producer workers) between farmer work actions; add tests for rest gating before next dispatch.

### 21.5 Farm storage and capacities

- [x] **T235**: Add failing tests for farm local storage capacity formula: L1=`3`, then `+1` slot every 2 levels (expected: L1-2=3, L3-4=4, L5-6=5, L7-8=6, L9-10=7).
- [x] **T236**: Implement/adjust farm storage capacity helpers and deposit guards so harvest deposit respects local capacity; when full, farmer cannot start new harvest cycle and reports blocked reason.

### 21.6 Transport queue integration (carrier)

- [x] **T237**: Add RED tests for transport task generation from farm local wheat storage into shared transport queue using existing priority rules (construction highest, then normal production logistics).
- [x] **T238**: Implement task emission for wheat export/import through current generic `TransportTask` pipeline; avoid per-frame duplicate spam (dedupe/throttle consistent with sawmill logic).
- [x] **T239**: Add edge-case tests for mid-route state changes (target full/no longer needs resource): carrier redirects/fallbacks using existing conventions, no task loss/deadlock.

### 21.7 UI, statuses, and player feedback

- [x] **T240**: Add/extend farm panel lines: local wheat storage `stored/capacity`, farmer status, blocked hints (no fields in radius, storage full, resting, moving, sowing, harvesting).
- [x] **T241**: Add field visual states for wheat phases (`PHASE_1..PHASE_4`) with disk-first assets + procedural fallback. Include render tests ensuring phase-specific sprite selection.
- [x] **T242**: Add action progress bars for farmer on field tile (sow/harvest) and verify draw order does not hide bar behind building sprites in common camera positions.

### 21.8 Regression, integration, and phase close

- [x] **T243**: Regression sweep for existing worker/building/pathfinding behavior (especially construction, sawmill, carriers, forester). Fix any breakages; run targeted tests while iterating.
- [x] **T244**: Add end-to-end smoke `tests/test_smoke_phase21.py`: place farm + several fields, build fields via builder, sow to `PHASE_4`, harvest to farm storage, carrier exports wheat via shared queue, ensure loop repeats.
- [x] **T245**: Final verification gate: full `pytest -q` + `ruff check src tests`; update Current Status and Notes; mark Phase 21 tasks; emit completion marker only when all tasks are `[x]`.

---

## Rules For Next Phase

- Keep exactly one active task marked `[~]` at a time.
- Start new work from the first unchecked `[ ]` task in the active phase.
- Mark `[x]` only after verification (`pytest -q`, and `ruff check src tests` when relevant).
- If blocked after repeated attempts, mark `[!]` and add a row in **Issues & Blockers**.

## Decisions Log

| Date | Task | Decision | Rationale |
|------|------|----------|-----------|
| | | | |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Extended history, completed phase checklists, and decisions log: **`progress_archive.md`**.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- T223 GREEN check: `pytest -q` passes after adding wheat lifecycle constants/helpers in `game.buildings.field`.
- T224 RED check: `pytest -q` fails because builder targets non-field tiles and never begins FIELD build (`construction_site.builder` remains `None`).
- T225 GREEN check: `pytest -q` passes with FIELD builder destination targeting the field tile itself; full suite green.
- T226 GREEN check: `pytest -q` passes with world-space FIELD build progress bar rendered only during active field construction.
- T227 RED check: `pytest -q` fails on missing `game.buildings.field.advance_wheat_growth` timing helper (45_000 ms steps).
- T228 GREEN check: `pytest -q` passes with deterministic 45-second phase advancement helper (`advance_wheat_growth`) and full suite green.
- T229 GREEN check: `pytest -q` passes with immediate harvest reset (`PHASE_4 -> EMPTY`) and sow-eligibility helper for same/next cycle selection.
- T230 RED check: `pytest -q` fails because farmer stays generic `working` and does not enter farm rest/field-cycle states.
- T231 RED check: `pytest -q` fails on missing farmer target selector (`select_farmer_field_target`) and no runtime priority dispatch yet.
- T232 GREEN check: `pytest -q` passes with farmer rest->target->harvest->return loop and priority selector wired in runtime; full suite green.
- T233 GREEN check: `pytest -q` passes with farmer empty-field sow action (`5_000 ms`) setting `PHASE_1` and returning to farm; full suite green.
- T234 GREEN check: `pytest -q` passes with explicit tests proving farmer remains in `resting` until rest timeout after sow and harvest actions.
- T235 RED check: `pytest -q` fails as expected on farm storage capacity formula (current `storage_capacity()` returns `5` at level 2, expected `3`).
- T236 GREEN check: `pytest -q` passes with farm-specific capacity ladder (`+1` every 2 levels) and farmer harvest dispatch blocked when farm storage is full.
- T237 RED check: `pytest -q` fails because no wheat export tasks are generated from farm local storage into the shared transport queue.
- T238 GREEN check: `pytest -q` passes with farm wheat export tasks emitted into shared queue and deduped per desired-count parity with current queue/in-flight tasks.
- T239 GREEN check: `pytest -q` passes with stale farm wheat tasks dropped after farm source empties mid-route while construction unavailable tasks remain queued for retry.
- T240 GREEN check: `pytest -q` passes with farm panel/status hints for `No fields in radius`, `Storage full`, `Resting`, `Moving`, `Sowing`, and `Harvesting`.
- T241 GREEN check: `pytest -q` passes with phase-specific FIELD sprite selection (`PHASE_1..PHASE_4`) and render test coverage.
- T242 GREEN check: `pytest -q` passes with farmer `sowing`/`harvesting` field-tile action bars rendered in worker overlay order and dedicated render test coverage.
- T243 GREEN check: targeted regression sweep passes (`pytest -q` on construction, sawmill, forester, workers, pathfinding, and transport suites: `107 passed`).
- T244 GREEN check: `tests/test_smoke_phase21.py` added and passing; fixed farmer `arrived_camp` deposit path so harvest now reaches farm storage and exports to Town Hall via carrier; full suite green (`504 passed`).
- T245 GREEN check: final verification gate passes (`pytest -q`: `504 passed`; `ruff check src tests`: `All checks passed!`); completion marker `.cursor/ralph/done` created.
