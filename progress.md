# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 29 - Localization EN/RU (**complete**)
- **Next Task:** (none — add Phase 30 when scoped)
- **Last Completed:** T468 - Close Phase 29
- **Total Progress:** 468 / 468 (Phase 29: 30 / 30 done)

> **Archive:** Phase 28 task details (T387–T438) and Phase 29 task details (T439–T468) are in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

**Phase 29 - Localization EN/RU** is complete (T439–T468). Full task text is in **`progress_archive.md`**.

Delivered:
- `game.i18n` loader with `en`/`ru` locale JSON under `src/game/settings/locales/`
- Cyrillic-capable `ui_font()`; player-facing UI migrated to `i18n.t()` keys
- Research and statue display copy externalized from balance JSON
- Locale completeness + RU layout smoke tests; **`localization_guide.md`**

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
| 2026-05-27 | T438 | Archive Phase 28 task log; keep agent contract in extension guides. | `progress.md` stays small for ralph-loop context; full T387-T438 list lives in `progress_archive.md`. |
| 2026-05-31 | Phase 29 | Put locale files under `src/game/settings/locales/`. | Keeps translation data beside existing game settings while separating translatable copy from gameplay balance. |
| 2026-05-31 | Phase 29 | Support `en` and `ru` first, with English as default fallback. | The current game copy is English; fallback keeps migration incremental and testable. |
| 2026-05-31 | Phase 29 | Centralize fonts and bundle a Cyrillic TTF loaded by path (T443). | Default pygame font lacks Cyrillic glyphs; delivery via `run.bat` runs from source, so no packaging step is needed. |
| 2026-05-31 | Phase 29 | No grammatical pluralization; counts shown as `label: N`. | Game copy uses `name: count` (e.g. `Дерево: 34`), so Russian plural forms are unnecessary. |
| 2026-05-31 | Phase 29 | Flat dotted i18n keys (e.g. `ui.button.start`) with `{param}` placeholders. | Flat keys make `en`/`ru` completeness diffing and missing-key checks trivial; the dotted convention namespaces by domain. |
| 2026-05-31 | Phase 29 | Locale-switch test harness lands early (T442), before any UI migration. | Migration tasks need isolated `ru` smoke without leaking global locale state; ordering follows Ralph backpressure best practice. |
| 2026-05-31 | T468 | Archive Phase 29 task log; keep contract in `localization_guide.md` and extension guides. | Same pattern as Phase 28; `progress.md` stays minimal for ralph-loop context. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| 2026-05-27 | Phase 28 | Exact Laboratory construction/upgrade costs and exact research costs/point requirements are balance values. | Use JSON-configured values; adjust when final balance is provided. |
| 2026-05-27 | Phase 28 | Concrete non-Technology research list and gameplay effects are not specified. | Out of scope for Phase 28 except for schema/framework support. |
| 2026-05-31 | Phase 29 | Russian strings are often longer than English and may overflow compact pygame UI controls. | Addressed by T465: fitted font sizing + `tests/test_locale_ru_layout.py`. |
| 2026-05-31 | Phase 29 | Default pygame font (`Font(None, …)`) has no Cyrillic glyphs, so Russian would render as empty boxes. | Addressed by T443: centralized font helper + bundled Cyrillic TTF loaded by path. |

## Notes

- Phase 28 delivered: unique `LABORATORY`, `SCIENTIST` (advanced School tab), top-bar Research screen, Technology chain `1`-`4`, carrier `laboratory_research` transport, in-run completion state (no save/load).
- Phase 29 delivered: full EN/RU localization via `game.i18n`, locale JSON, UI migration, completeness/layout tests, and **`localization_guide.md`**.
- Keep completed phase task lists in `progress_archive.md`; `progress.md` stays focused on the active phase for ralph-loop context.
- Localization target folder: **`src/game/settings/locales/`**; rules: **`localization_guide.md`**.
- Initial locale ids: `en`, `ru`; English is the default fallback.
- UI font: single bundled Cyrillic-capable TTF via a shared font helper (see T443); `Font(None, …)` must not be used in UI code.
- Delivery is via **`run.bat`** (venv + run from source); `build_exe.bat`/`game.spec` is not the actual build path and bundles no `datas`.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Laboratory / Research extension rules: **`research_extension_guide.md`**.
- Worker effects rules: **`worker_effects_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task in the active phase.
