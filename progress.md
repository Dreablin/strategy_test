# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 21 — Wheat fields + farmer field cycle
- **Next Task:** T226 — FIELD construction progress bar render support
- **Last Completed:** T225 — Implement FIELD construction specialization
- **Total Progress:** 225 / 245 (Phase 19: 25 / 25 done; Phase 20: 11 / 11 done; Phase 21: 5 / 25 done)

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
- [ ] **T226**: Add rendering/UI support for FIELD construction progress bar under builder while building (on-map world progress bar). Include headless render test that verifies bar appears only during FIELD build.

### 21.3 Wheat growth runtime

- [ ] **T227**: Add failing tests for wheat autonomous growth timing on built fields: `PHASE_1 -> PHASE_2 -> PHASE_3 -> PHASE_4`, each step every `45_000 ms`, growth pauses only if field is not sown.
- [ ] **T228**: Implement runtime growth updater (world/worker manager tick path): deterministic timestamp-based progression using existing `now_ms` flow; no per-frame floating accumulation drift.
- [ ] **T229**: Add tests + implementation for harvest reset: when farmer harvests `PHASE_4`, field becomes `EMPTY` immediately and can be selected for sowing in the same/next farmer cycle.

### 21.4 Farmer behavior cycle (Farm worker AI)

- [ ] **T230**: Add RED tests for farmer assignment lifecycle: after hire farmer enters farm, rests, then starts field work cycles from farm home base.
- [ ] **T231**: Add RED tests for farmer target selection priority within radius **10** (Chebyshev) from assigned farm:  
  1) pick ripe field (`PHASE_4`) first;  
  2) if none, pick empty field (`EMPTY`) for sowing;  
  3) if neither exists, stay/rest and retry later.
- [ ] **T232**: Implement farmer navigation + action loop for **harvest** action: move to target field tile, perform `5_000 ms` action with progress bar, then carry wheat back to farm local storage.
- [ ] **T233**: Implement farmer navigation + action loop for **sow** action: move to empty field tile, perform `5_000 ms` action with progress bar, set field to `PHASE_1`, return to farm.
- [ ] **T234**: Integrate standard post-action rest cycle (same rest semantics as other producer workers) between farmer work actions; add tests for rest gating before next dispatch.

### 21.5 Farm storage and capacities

- [ ] **T235**: Add failing tests for farm local storage capacity formula: L1=`3`, then `+1` slot every 2 levels (expected: L1-2=3, L3-4=4, L5-6=5, L7-8=6, L9-10=7).
- [ ] **T236**: Implement/adjust farm storage capacity helpers and deposit guards so harvest deposit respects local capacity; when full, farmer cannot start new harvest cycle and reports blocked reason.

### 21.6 Transport queue integration (carrier)

- [ ] **T237**: Add RED tests for transport task generation from farm local wheat storage into shared transport queue using existing priority rules (construction highest, then normal production logistics).
- [ ] **T238**: Implement task emission for wheat export/import through current generic `TransportTask` pipeline; avoid per-frame duplicate spam (dedupe/throttle consistent with sawmill logic).
- [ ] **T239**: Add edge-case tests for mid-route state changes (target full/no longer needs resource): carrier redirects/fallbacks using existing conventions, no task loss/deadlock.

### 21.7 UI, statuses, and player feedback

- [ ] **T240**: Add/extend farm panel lines: local wheat storage `stored/capacity`, farmer status, blocked hints (no fields in radius, storage full, resting, moving, sowing, harvesting).
- [ ] **T241**: Add field visual states for wheat phases (`PHASE_1..PHASE_4`) with disk-first assets + procedural fallback. Include render tests ensuring phase-specific sprite selection.
- [ ] **T242**: Add action progress bars for farmer on field tile (sow/harvest) and verify draw order does not hide bar behind building sprites in common camera positions.

### 21.8 Regression, integration, and phase close

- [ ] **T243**: Regression sweep for existing worker/building/pathfinding behavior (especially construction, sawmill, carriers, forester). Fix any breakages; run targeted tests while iterating.
- [ ] **T244**: Add end-to-end smoke `tests/test_smoke_phase21.py`: place farm + several fields, build fields via builder, sow to `PHASE_4`, harvest to farm storage, carrier exports wheat via shared queue, ensure loop repeats.
- [ ] **T245**: Final verification gate: full `pytest -q` + `ruff check src tests`; update Current Status and Notes; mark Phase 21 tasks; emit completion marker only when all tasks are `[x]`.

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
