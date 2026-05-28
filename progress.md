# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 28 - Laboratory and Research (**complete**)
- **Next Task:** None — all tasks through T438 are complete
- **Last Completed:** T438 - Close Phase 28 progress only
- **Total Progress:** 438 / 438 (Phase 28: 52 / 52 done)

> **Archive:** Phase 28 task details (T387–T438) are in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

**Phase 28 — Laboratory and Research** is **complete** (52 tasks, T387–T438). Implementation covers `LABORATORY`, `SCIENTIST`, JSON-driven researches, carrier delivery, Scientist point production, full-screen Research UI, and `research_extension_guide.md`. Add a new phase section here when the PRD defines the next scope.

- [x] **T438**: Close Phase 28 progress only.

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
| 2026-05-27 | T438 | Archive Phase 28 task log; keep agent contract in extension guides. | `progress.md` stays small for ralph-loop context; full T387–T438 list lives in `progress_archive.md`. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| 2026-05-27 | Phase 28 | Exact Laboratory construction/upgrade costs and exact research costs/point requirements are balance values. | Use JSON-configured values; adjust when final balance is provided. |
| 2026-05-27 | Phase 28 | Concrete non-Technology research list and gameplay effects are not specified. | Out of scope for Phase 28 except for schema/framework support. |

## Notes

- Phase 28 delivered: unique `LABORATORY`, `SCIENTIST` (advanced School tab), top-bar Research screen, Technology chain `1`–`4`, carrier `laboratory_research` transport, in-run completion state (no save/load).
- Keep completed phase task lists in `progress_archive.md`; `progress.md` stays minimal until a new phase is defined.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Laboratory / Research extension rules: **`research_extension_guide.md`**.
- Worker effects rules: **`worker_effects_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
