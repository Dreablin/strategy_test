# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 15 — Housing, House, School training queue, population HUD
- **Next Task:** None (all tasks complete)
- **Last Completed:** T173 — final verification + phase close
- **Total Progress:** 173 / 173 (Phase 15: 13 / 13 tasks done)

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

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Extended history and completed phase checklists: **`progress_archive.md`**.
- After Phase 13, orthogonal paths are longer than diagonal-allowing BFS; **F-PATH** / **F-WORK-07** in PRD match **4-dir** `find_path_bfs`.
