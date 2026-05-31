# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 29 - Localization EN/RU (**in progress**)
- **Next Task:** T467 - Finalize localization docs
- **Last Completed:** T466 - Update tests to use i18n keys
- **Total Progress:** 466 / 468 (Phase 29: 28 / 30 done)

> **Archive:** Phase 28 task details (T387-T438) are in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

**Phase 29 - Localization EN/RU** migrates player-facing text out of Python/runtime balance files into dedicated locale files. Initial supported languages are English (`en`) and Russian (`ru`). Locale files must live under **`src/game/settings/locales/`**. Keep gameplay/balance JSON separate from translatable copy where practical.

### Phase 29 working agreement (read before every task)

Each task runs in a fresh context. Do not assume prior memory; read this block, the task text, and the named files from disk.

- **i18n entry point:** all player-facing strings render through `game.i18n.t(key, **params)` (created in T441). Never re-introduce raw literals in UI/runtime once a module is migrated.
- **Key naming convention** (defined in T439, used by all later tasks):
  - `ui.button.<name>` (e.g. `ui.button.start`, `ui.button.upgrade`, `ui.button.demolish`, `ui.button.close`, `ui.button.back`)
  - `ui.common.<name>` (e.g. `ui.common.active`, `ui.common.inactive`, `ui.common.cost`, `ui.common.status`, `ui.common.storage`, `ui.common.requirements`)
  - `resource.<id>` (e.g. `resource.wood`, `resource.simple_meal`)
  - `worker.<TYPE>` (e.g. `worker.CARRIER`)
  - `building.<TYPE>.name`, `building.<TYPE>.desc`
  - `status.<id>` for production/worker statuses (e.g. `status.ready`, `status.output_full`)
  - `research.<id>.name`, `research.<id>.desc`, `research.<id>.effect`
  - `statue.stage.<n>` (n = 1..4)
- **Counts use `label: N` format** (e.g. `Дерево: 34`). No grammatical pluralization.
- **ids/enums never change.** Only the displayed text moves to locales. Resource keys, `type_tag`s, worker/state ids, research ids stay as-is.
- **Backpressure (run before marking any task `[x]`):**
  - Targeted: `pytest -q tests/<file>.py` for the tests named in the task.
  - Full suite: `pytest -q` (must stay green; default locale is `en`).
  - When adding new files: `ruff check src tests`.
  - Tests are headless (`SDL_VIDEODRIVER=dummy` via `tests/conftest.py`); the default test locale is `en` unless a test explicitly switches it via the T442 harness.
- **Locale switching in tests** must use the T442 harness (no leaking global locale state across tests).
- **Fallback:** missing `ru` key → fall back to `en`; missing `en` key → return the key id (loud, so it is caught).

- [x] **T439**: Define i18n key schema and contract (design + tiny validation test).
  - Write the contract as a short doc section in `localization_guide.md` (new file at repo root) capturing the key naming convention from the working agreement above, `{param}` placeholder syntax, and fallback rules (`ru`→`en`→key id).
  - Decide JSON shape: nested objects keyed by dotted segments OR flat dotted keys. Pick **flat dotted keys** (e.g. `"ui.button.start": "Start"`) for simple diffing and completeness checks; record this choice.
  - Create empty/seed `src/game/settings/locales/en.json` and `src/game/settings/locales/ru.json` containing only 2-3 sample keys (`ui.button.start`, `resource.wood`, `research.1.name`) to prove the shape can express button, resource, and research copy.
  - Add `tests/test_i18n_schema.py` that loads both files as JSON, asserts they parse, and asserts the sample keys exist in both.
  - Verify: `pytest -q tests/test_i18n_schema.py`; `ruff check src tests`; then `pytest -q`.
  - Acceptance: schema doc exists, both locale files parse, sample-key test passes.
- [x] **T440**: Add failing loader tests for `game.i18n` (RED).
  - Create `tests/test_i18n_loader.py` covering: load default locale (`en`), load explicit locale (`ru`), `t("ui.button.start")` returns the English string, `t(<key only in en>)` from `ru` falls back to English, `t(<missing key>)` returns the key id, and `{param}` substitution via `t("x.y", name="Дерево")`.
  - These tests import `from game import i18n` which does not exist yet, so they must fail (RED). Do not implement the module in this task.
  - Verify: `pytest -q tests/test_i18n_loader.py` and confirm it fails for the expected (import/attribute) reason, not a syntax error in the test.
  - Acceptance: `test_i18n_loader.py` exists and is RED; the rest of the suite is unaffected (`pytest -q` shows only these new failures).
- [x] **T441**: Implement `game.i18n` loader + current-locale selection (GREEN).
  - Create `src/game/i18n.py` with: `t(key: str, **params) -> str`, `set_locale(code: str)`, `get_locale() -> str`, and a loader that reads `src/game/settings/locales/<code>.json`.
  - Default locale comes from a new optional `"locale"` key in `game_settings.json` (add `"locale": "en"`), defaulting to `en` when absent.
  - Fallback chain: requested locale → `en` → return key id. `{param}` substitution via `str.format(**params)`; on `KeyError`/missing param, return the unformatted template (do not crash).
  - Make all `test_i18n_loader.py` tests from T440 pass.
  - Verify: `pytest -q tests/test_i18n_loader.py tests/test_i18n_schema.py`; `ruff check src tests`; then `pytest -q`.
  - Acceptance: loader tests are GREEN and full suite passes.
- [x] **T442**: Add a locale-switch test harness (used by all later `ru`-smoke tests).
  - Add a pytest fixture/context manager in `tests/conftest.py` (e.g. `use_locale`) that calls `i18n.set_locale(code)` and restores the previous locale on exit, so no global locale state leaks between tests.
  - Add `tests/test_i18n_harness.py` proving the same key returns English then Russian inside two isolated `use_locale` blocks, and that the locale is restored to `en` afterward.
  - Verify: `pytest -q tests/test_i18n_harness.py`; then `pytest -q`.
  - Acceptance: harness exists, isolation test passes, no other test changes behavior.
- [x] **T443**: Centralize font creation and bundle a Cyrillic-capable font.
  - Create `src/game/ui/fonts.py` with a cached helper `ui_font(size: int) -> pygame.font.Font` that loads one bundled TTF by path.
  - Add a Unicode TTF with full Cyrillic coverage under `assets/fonts/` (e.g. DejaVuSans). Load it relative to the package, falling back to `pygame.font.Font(None, size)` only if the file is missing.
  - Replace every `pygame.font.Font(None, size)` call in `src/game/ui/*.py`, `src/game/render.py`, and `src/game/assets.py` with `ui_font(size)`. (Use `rg "Font\(None" src` to find all sites.)
  - No packaging step is required: delivery is via `run.bat` (runs from source with `PYTHONPATH=src`). The optional `game.spec`/`build_exe.bat` build is not the actual delivery path and bundles no `datas`.
  - Add `tests/test_ui_fonts.py`: `ui_font(22).render("Дерево", True, (255,255,255))` returns a surface with `get_width() > 0`, and confirm no `Font(None` remains via the test or a documented allowlist.
  - Verify: `pytest -q tests/test_ui_fonts.py`; `ruff check src tests`; then `pytest -q`.
  - Acceptance: Cyrillic renders to a non-empty surface; all panels use `ui_font`; full suite passes.
- [x] **T444**: Seed shared/common locale keys (`ui.*`).
  - Add to both locale files: `ui.button.{start,upgrade,demolish,close,back}`, `ui.common.{active,inactive,cost,status,storage,requirements,free,unavailable}`, and `ui.window.caption` (en: `Isometric Strategy`). Provide Russian values for all.
  - Apply `ui.window.caption` in `main.py` (replace the literal in `pygame.display.set_caption(...)` with `i18n.t("ui.window.caption")`).
  - Verify: `pytest -q tests/test_i18n_schema.py`; smoke `python -c "import game.main"`; then `pytest -q`.
  - Acceptance: both files contain all listed keys with non-empty values; caption uses i18n.
- [x] **T445**: Migrate resource display labels (`resource.<id>`) — `src/game/resource_catalog.py`.
  - Replace the body of `resource_display_label` and `_DISPLAY_LABEL_OVERRIDES` with an i18n lookup: `t(f"resource.{key}")`, where `key` is the lowercased resource id; keep current fallback (`key.replace("_"," ").title()`) when the locale has no entry.
  - Add `resource.*` keys to both locales for every id in `TOWN_HALL_WAREHOUSE_KEYS` plus `simple_meal`, `elite_meal`, `water` (en values: current Title-Case; `Simple meal`, `Elite meal`).
  - Update/extend `tests/test_elite_meal_resource.py`; cover `wood`, `simple_meal`, `elite_meal`, and an unknown id fallback, with a `ru` smoke using the harness.
  - Verify: `pytest -q tests/test_elite_meal_resource.py`; then `pytest -q`.
  - Acceptance: labels come from locales; ids unchanged; tests pass `en`+`ru`.
- [x] **T446**: Migrate worker display labels (`worker.<TYPE>`) — `src/game/ui/worker_labels.py`.
  - Replace `WORKER_LABEL` dict usage in `worker_display_label` with `t(f"worker.{key}")`, keeping the `.title()` fallback. Keep `building_worker_status_line` format but route the `Worker`/`Worker (label)` words through `ui.*`/`worker.*` keys.
  - Add `worker.<TYPE>` keys to both locales for every type in `WORKER_LABEL` (all 15 listed).
  - Update `tests/test_winemaker_display.py` and `tests/test_scientist_display.py`; add a parametrized test covering every `HIRABLE_WORKERS` type in `en` and `ru`.
  - Verify: `pytest -q tests/test_winemaker_display.py tests/test_scientist_display.py`; then `pytest -q`.
  - Acceptance: every worker type has localized labels in both locales; tests pass.
- [x] **T447**: Migrate building names + descriptions (`building.<TYPE>.name/.desc`) — `src/game/ui/building_panel.py`.
  - Replace `_DISPLAY_NAME` and `_DESCRIPTION` lookups with `t(f"building.{tag}.name")` / `t(f"building.{tag}.desc")`.
  - Add `building.<TYPE>.name` and `.desc` keys for every registered building type (the 17 names in `_DISPLAY_NAME` plus `MILL`, which has a description but no name entry — add a `MILL` name). Use existing English strings verbatim.
  - Update `tests/test_building_panel.py`; assert localized name/desc for at least `TOWN_HALL`, `LABORATORY`, `STATUE` in `en` and one `ru` smoke.
  - Verify: `pytest -q tests/test_building_panel.py`; then `pytest -q`.
  - Acceptance: all building types resolve a non-empty localized name; tests pass.
- [x] **T448**: Localize bottom build menu + cost tooltip — `src/game/ui/bottom_bar.py`.
  - Route category/building button labels (`_RESOURCE_BUTTONS`, `_FOOD_BUTTONS`, and the inline lists `School/House/Canteen/Restaurant/Laboratory/Statue`, `Sawmill/Mill/Bakery/...`) through `building.<TYPE>.name` (T447) so labels are not duplicated.
  - Route the cost tooltip words `Cost:`, `Cost: Free`, `Cost: unavailable` through `ui.common.*` keys; keep `{resource_display_label}: {n}` lines.
  - Localize the statue research requirement line text.
  - Update `tests/test_bottom_bar_menu.py`; assert English defaults and a `ru` lookup smoke.
  - Verify: `pytest -q tests/test_bottom_bar_menu.py`; then `pytest -q`.
  - Acceptance: bottom-bar labels/tooltips come from locales; tests pass.
- [x] **T449**: Localize top bar — `src/game/ui/top_bar.py`.
  - Replace `_RESEARCH_BTN_LABEL = "Research"` with `t("ui.topbar.research")`; template the population label `"{current} (max {max})"` and the deliveries label `"Deliveries: {n} (in progress {k})"` via i18n templates with `{param}` placeholders.
  - Add `ui.topbar.*` keys (research button, population template, deliveries template) to both locales.
  - Update the top-bar layout test (find via `rg "TopBar" tests`); assert layout still computes and `{param}` substitution is exercised in `en` and `ru`.
  - Verify: run the top-bar test file; then `pytest -q`.
  - Acceptance: top-bar text from locales; layout tests pass; templates tested.
- [x] **T450**: Localize base building panel actions + Town Hall panel.
  - In `building_panel.py`: route `_upgrade_label` (`Start stage: {stage}`, `Upgrade to Lv {n}`), `_upgrade_cost_lines` words, demolish/close/status/storage words, and the statue stage upgrade text through `ui.*`/`building.*`/`statue.*` keys.
  - In `src/game/ui/town_hall_panel.py`: route the panel title and warehouse resource labels through `building.TOWN_HALL.name` / `resource.<id>`.
  - Update `tests/test_building_panel.py` and `tests/test_town_hall_panel.py`; cover upgrade label for a normal building and the statue stage label.
  - Verify: `pytest -q tests/test_building_panel.py tests/test_town_hall_panel.py`; then `pytest -q`.
  - Acceptance: building-panel, town-hall-panel, and statue-panel tests pass with localized text.
- [x] **T451**: Localize construction panel — `src/game/ui/construction_panel.py`.
  - Route title line, requirements header, delivered counters, builder state, progress, demolish, active/inactive, and the statue delivery toggle through `ui.*`/`status.*`/`statue.*` keys; keep numeric `{n}/{m}` formats.
  - Update `tests/test_*construction*` (find via `rg -l construction tests`); cover a regular building and statue construction in `en`, plus one `ru` smoke.
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: construction-panel tests pass for regular + statue.
- [x] **T452**: Localize worker panel — `src/game/ui/worker_panel.py`.
  - Route state labels, satiety, movement speed, assignment, carrying, task, from/to, returning, and resource names through `status.*`/`ui.*`/`resource.*`/`worker.*` keys.
  - Update the worker-panel test (find via `rg -l worker_panel tests`); add a `ru` smoke for one worker.
  - Verify: run the worker-panel test file; then `pytest -q`.
  - Acceptance: worker-panel tests pass; one `ru` smoke included.
- [x] **T453**: Localize population panel — `src/game/ui/population_panel.py`.
  - Route title, filters, worker rows, assignment/task detail labels, and any empty-state text through `ui.*`/`status.*`/`worker.*` keys (note the local `"sowing": "Sowing"` style map at the top of the module).
  - Update the population-panel test (find via `rg -l population_panel tests`); ensure click/scroll behavior tests do not regress.
  - Verify: run the population-panel test file; then `pytest -q`.
  - Acceptance: population-panel tests pass; interaction behavior unchanged.
- [x] **T454**: Externalize production/worker status strings (`status.<id>`) — `src/game/worker_status.py`.
  - This module returns ~25 distinct human-readable strings (`Ready`, `Resting`, `Processing`, `No worker`, `Inactive`, `Output full`, `Storage full`, `Under construction`, `No wood/wheat/flour/water/chicken/bread/grain/grapes`, `Missing inputs`, `Moving`, `Sowing`, `Harvesting`, `Mining`, `On the way`, `Gathering`, `Depositing`, `At resource`, `At camp`, `Waiting target`, `No fields in radius`, `No ripe vineyards in range`, `Unknown`, etc.).
  - Decide a stable status-id scheme: keep the functions returning stable English ids OR introduce `status.<id>` keys and localize at the panel boundary. Prefer adding `status.<snake_id>` locale keys and a single `localized_status(s)` helper so panels render localized text while tests can still assert ids.
  - Map every returned string to a `status.*` key in both locales.
  - Update the status-helper test (find via `rg -l worker_status tests`); assert localized output for a few representative statuses in `en`+`ru`.
  - Verify: run the status test file; then `pytest -q`.
  - Acceptance: every status string has a locale key; tests assert consistent ids/output.
- [x] **T455**: Localize raw + processing building panels.
  - Files: `lumber_camp_panel.py`, `stone_mine_panel.py`, `iron_mine_panel.py`, `forester_hut_panel.py`, `well_panel.py`, `sawmill_panel.py`, `mill_panel.py`, `bakery_panel.py`, `winery_panel.py`.
  - Route their visible text — `Active`/`Inactive` toggles, `Demolish`, storage lines like `Grapes: {n} / {m}` / `Wine: {n} / {m}`, and any status text — through `ui.*`/`status.*`/`resource.*` keys. Resource/amount labels reuse `resource.<id>`.
  - Update the relevant panel tests (find via `rg -l "sawmill\|winery\|forester\|well_panel\|mill_panel\|bakery" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: no hard-coded visible English remains in these modules except ids/constants; tests pass.
- [x] **T456**: Localize Laboratory panels — `src/game/ui/laboratory_panel.py` + `laboratory_panel_research.py`.
  - Route `Scientists: {n} / {m}`, `Upgrade to Lv {n}`, slot labels `Empty`/`Sci`, `Active`/`Inactive`, `Active research`, and the research points line (`{current} / {required}`) through `ui.*`/`status.*`/`building.LABORATORY.*` keys.
  - Update `tests/test_laboratory_panel.py` and `tests/test_laboratory_labels.py`; add a `ru` smoke for the scientists line.
  - Verify: `pytest -q tests/test_laboratory_panel.py tests/test_laboratory_labels.py`; then `pytest -q`.
  - Acceptance: laboratory panel tests pass with localized text.
- [x] **T457**: Localize food/dining panels.
  - Files: `farm`-related panel, `vineyard_farm_panel.py`, `canteen_panel.py`, `restaurant_panel.py`, `chicken_farm_panel.py`, `cow_farm_panel.py`.
  - Route dining slot/status text, blocked reasons, and meal/resource labels through `status.*`/`resource.*`/`ui.*` keys. Meal labels reuse `resource.simple_meal` / `resource.elite_meal`.
  - Update the relevant panel tests (find via `rg -l "canteen\|restaurant\|chicken_farm\|cow_farm\|vineyard_farm" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: relevant panel tests pass; meal/resource labels come from locale paths.
- [x] **T458**: Localize school panel — `src/game/ui/school_panel.py`.
  - Route title, queue, Basic/Advanced tab labels, hire/cancel labels, worker labels (reuse `worker.<TYPE>`), and upgrade/demolish through `ui.*`/`worker.*` keys.
  - Update `tests/test_laboratory_menu.py` / school-panel tests (find via `rg -l school_panel tests`); assert Basic/Advanced tab labels in `en` and `ru`.
  - Verify: run the school-panel test file; then `pytest -q`.
  - Acceptance: school-panel tests pass for tab labels in both locales.
- [x] **T459**: Externalize research copy from `src/game/settings/research.json` (`research.<id>.*`).
  - Move each research's `name`, `description`, `effect_text` into `research.<id>.name/.desc/.effect` locale keys (ids include `1`, `carrier_speed_1`, `statue_excavation`, etc.). Keep ids, `resource_cost`, `required_points`, `tier`, `column`, `dependencies`, `image_key`, `worker_effects` in `research.json`.
  - Update `research_config.py`/loaders to read display copy from i18n by id; if the JSON still carries `name`/etc., have the loader prefer the locale and treat JSON text as a dev-only fallback (or remove it — record the choice).
  - Update research config tests (find via `rg -l research_config tests`) to validate the balance schema still loads; assert localized `name`/`effect` via i18n.
  - Verify: run research config/test files; `ruff check src tests`; then `pytest -q`.
  - Acceptance: balance schema still validates; UI copy resolves through i18n for every research id.
- [x] **T460**: Localize research screen + tooltip + start button.
  - Files: `research_screen.py` (`_TITLE = "Research"`, `Technology`, `Tier {n}`), `research_tile_tooltip.py` (`Cost`/`Points`/`Requires`/`Effect`/`Locked`, dependency names), `research_start_button.py` (`Start`).
  - Route all through `ui.research.*` keys; dependency and research names reuse `research.<id>.name` (T459).
  - Update tests (find via `rg -l "research_screen\|research_tile_tooltip\|research_start_button\|research_tile" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: research screen, tooltip, and start-button tests pass.
- [x] **T461**: Externalize statue stage names from `src/game/settings/buildings/statue.json` (`statue.stage.<n>`).
  - Move `stage_names` (`1:Excavation`, `2:Foundation`, `3:Pedestal`, `4:Statue`) to `statue.stage.1..4` locale keys. Keep `footprint`, `levels`, costs, `build_time_ms` in JSON.
  - Update `Statue.stage_name` (`src/game/buildings/statue.py`) to resolve via i18n, keeping the `Stage {n}` fallback.
  - Update `tests/test_statue.py`; assert English stage names and a `ru` stage-name smoke.
  - Verify: `pytest -q tests/test_statue.py`; then `pytest -q`.
  - Acceptance: statue stage names resolve through i18n in both locales.
- [x] **T462**: Localize lock reasons / requirement messages shown in UI.
  - Cover research eligibility reasons, laboratory requirement messages, active-research messages, and statue requirement messages (find sources via `rg -n "requires\|locked\|need\|requirement" src/game`).
  - Route through `ui.lock.*` / `status.*` keys, or keep stable reason ids localized at the UI boundary; record the approach.
  - Update the lock-reason tests (find via `rg -l "lock\|requirement\|eligib" tests`).
  - Verify: run those test files; then `pytest -q`.
  - Acceptance: lock/requirement messages compare localized strings or stable reason ids in tests.
- [x] **T463**: Enforce Russian locale completeness.
  - Add `tests/test_locale_completeness.py` that loads `en.json` and `ru.json` and asserts identical key sets, no missing values, and no empty/whitespace-only strings.
  - Fill any `ru` gaps the test surfaces.
  - Verify: `pytest -q tests/test_locale_completeness.py`; then `pytest -q`.
  - Acceptance: `en` and `ru` key sets match exactly; no empty values.
- [x] **T464**: Audit remaining player-facing literals in `src/game`.
  - Use `rg` to find remaining quoted human text in `src/game/ui`, `src/game/render.py`, `worker_status.py`, and runtime modules (e.g. `rg -n "\"[A-Z][a-z].*\"" src/game/ui`).
  - Migrate any genuine UI strings missed by earlier tasks; document a short allowlist (dev-only text like `dev_asset_reload.py`, ids/enums, log strings) in `localization_guide.md`.
  - Verify: `pytest -q`.
  - Acceptance: documented allowlist exists; no obvious UI strings remain outside locale files.
- [x] **T465**: Verify layout with Russian text.
  - Add headless render smoke checks under the `ru` locale (via T442 harness) for: bottom bar, building panel, worker panel, research screen, construction panel. Assert text surfaces fit within their target rects (no overflow beyond panel bounds).
  - Adjust widths/wrapping only where overflow is detected; do not restyle otherwise.
  - Verify: run the new layout test(s); then `pytest -q`.
  - Acceptance: no overflow in tested surfaces under `ru`.
- [x] **T466**: Update tests that still assume English literals.
  - Sweep the suite for assertions on raw English text that should be key-based or locale-controlled; convert them to assert via `t(key)` or under an explicit `en` harness block.
  - Verify: `pytest -q` (default `en` locale) passes fully.
  - Acceptance: full suite green; no brittle English-literal assertions remain for migrated modules.
- [ ] **T467**: Finalize localization docs.
  - Complete `localization_guide.md`: locale folder, flat dotted-key naming, `{param}` syntax, fallback behavior, how to add a new language, and how tests switch locale (T442 harness).
  - Cross-link from `building_extension_guide.md`, `worker_extension_guide.md`, and `research_extension_guide.md` that new player-facing strings must go through `game.i18n` keys.
  - Verify: `python -c "import game.i18n"`; then `pytest -q`.
  - Acceptance: docs describe `src/game/settings/locales/`, key naming, and test expectations.
- [ ] **T468**: Close Phase 29.
  - Run full verification (`pytest -q`; `ruff check src tests`).
  - Update Current Status, Decisions Log, Issues & Blockers, and archive Phase 29 task detail if the list grows too large.

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

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| 2026-05-27 | Phase 28 | Exact Laboratory construction/upgrade costs and exact research costs/point requirements are balance values. | Use JSON-configured values; adjust when final balance is provided. |
| 2026-05-27 | Phase 28 | Concrete non-Technology research list and gameplay effects are not specified. | Out of scope for Phase 28 except for schema/framework support. |
| 2026-05-31 | Phase 29 | Russian strings are often longer than English and may overflow compact pygame UI controls. | Include layout smoke tests and adjust wrapping/sizing during localization tasks. |
| 2026-05-31 | Phase 29 | Default pygame font (`Font(None, …)`) has no Cyrillic glyphs, so Russian would render as empty boxes. | Addressed by T443: centralized font helper + bundled Cyrillic TTF loaded by path. |

## Notes

- Phase 28 delivered: unique `LABORATORY`, `SCIENTIST` (advanced School tab), top-bar Research screen, Technology chain `1`-`4`, carrier `laboratory_research` transport, in-run completion state (no save/load).
- Keep completed phase task lists in `progress_archive.md`; `progress.md` stays focused on the active phase for ralph-loop context.
- Localization target folder: **`src/game/settings/locales/`**.
- Initial locale ids: `en`, `ru`; English is the default fallback.
- UI font: single bundled Cyrillic-capable TTF via a shared font helper (see T443); `Font(None, …)` must be phased out.
- Delivery is via **`run.bat`** (venv + run from source); `build_exe.bat`/`game.spec` is not the actual build path and bundles no `datas`.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Laboratory / Research extension rules: **`research_extension_guide.md`**.
- Worker effects rules: **`worker_effects_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
