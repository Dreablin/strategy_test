# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 5. Building Panel & Actions
- **Next Task:** T30 — Implement town hall panel UI
- **Last Completed:** T29 — Implement demolish action and worker idle hooks
- **Total Progress:** 29 / 42

---

## Task Log

### Phase 1 — Project Foundation

- [x] **T01**: Create project skeleton — `src/game/`, `tests/`, `requirements.txt` (pygame 2.5.2, pytest 8.3.3, pyinstaller 6.10.0, ruff 0.6.9), `pyproject.toml` (pytest config: `testpaths=["tests"]`), `.gitignore` (add `.cursor/ralph/`, `__pycache__/`, `*.pyc`, `build/`, `dist/`, `*.spec.bak`), empty `README.md` placeholder, empty `src/game/__init__.py` and `tests/__init__.py`. Verify `pip install -r requirements.txt` succeeds and `pytest -q` runs (0 tests, exits 0).
- [x] **T02**: Write `tests/conftest.py` setting `os.environ["SDL_VIDEODRIVER"]="dummy"` BEFORE any pygame import; add a `pygame_initialized` autouse fixture that calls `pygame.init()` / `pygame.quit()` per session. Verify with `pytest -q` (still 0 tests, exits 0).
- [x] **T03**: Write `tests/test_config.py` asserting required constants exist with sane values: `TICK_MS == 10_000`, `TILE_W == 64`, `TILE_H == 32`, `GRID_SIZE == 32`, `INITIAL_RESOURCES == {"food":200,"wood":200,"stone":0,"iron":0}`, `WORKER_HIRE_COST == {"food":50}`, `BUILD_COST_WOOD == 100`, `MAX_LEVEL == 10`, `WINDOW_SIZE == (1280, 720)`. Tests must FAIL (module not yet implemented).
- [x] **T04**: Implement `src/game/config.py` with all constants from T03. Run `pytest tests/test_config.py -q` — must PASS.
- [x] **T05**: Write `tests/test_iso.py` covering `world_to_screen` and `screen_to_world` round-trip for grid points (0,0), (1,0), (0,1), (5,7), (31,31). Tests must FAIL.
- [x] **T06**: Implement `src/game/iso.py` with classic 2:1 isometric transform using `TILE_W=64`, `TILE_H=32`. `screen_to_world` returns int grid coords. Run tests — must PASS.
- [x] **T07**: Implement `src/game/main.py` with a clean `def main()` that opens a 1280×720 pygame window titled "Isometric Strategy", runs a 60 FPS loop until QUIT, then `pygame.quit()` and `return`. Smoke-test with `SDL_VIDEODRIVER=dummy timeout 2 python -m game.main || true` (exits cleanly).

### Phase 2 — Resources & Top Bar

- [x] **T08**: Write `tests/test_resources.py` covering: initial values, `add` increments, `has`/`try_spend` for cost dicts, `try_spend` returns False & does not deduct on insufficient funds, non-negative invariants. Tests must FAIL.
- [x] **T09**: Implement `src/game/resources.py` (`ResourceManager`). Run tests — must PASS.
- [x] **T10**: Write `tests/test_tick.py` covering `TickScheduler.update(now_ms)`: returns True exactly once per 10_000 ms boundary; returns False otherwise. Tests must FAIL.
- [x] **T11**: Implement `src/game/tick.py` (`TickScheduler`). Run tests — must PASS.
- [x] **T12**: Implement `src/game/assets.py` — pure-pygame procedural factory: `grass_tile()`, `tree_tile()`, `building_sprite(b_type, level)`, `worker_dot(w_type)`, `resource_icon(name)`. Returns cached `pygame.Surface`. Add a tiny smoke test `tests/test_assets.py` checking each function returns a non-empty Surface (uses `SDL_VIDEODRIVER=dummy`). Tests must PASS after implementation.
- [x] **T13**: Implement `src/game/ui/top_bar.py` — `TopBar.draw(surface, resources)` renders the 4 resources in a 48 px strip using `assets.resource_icon` and current `amount` and `(+income)`. Manual smoke check: `python -c "from game.ui.top_bar import TopBar; print('ok')"`.

### Phase 3 — World & Rendering

- [x] **T14**: Write `tests/test_world.py` covering: grid is 32×32, `is_in_grass(gx,gy)` correct, `mark_occupied`/`is_occupied`/`free` work, footprint occupancy spans all tiles. Tests must FAIL.
- [x] **T15**: Implement `src/game/world.py` (`World` with grid + occupancy bitmap + grass/tree zones). Run tests — must PASS.
- [x] **T16**: Implement `src/game/render.py` — `Renderer.draw_world(surface, world)` draws grass diamonds for every in-grass tile and tree borders outside grass. Smoke check by running main loop briefly under dummy driver.
- [x] **T17**: Wire `World` + `Renderer` into `main.py` so launching the game shows the grass field with tree borders. Visual confirmation only (no test).

### Phase 4 — Buildings & Placement

- [x] **T18**: Write `tests/test_costs.py` covering `upgrade_cost(L)` for L=1..10. Specifically:
   - L→2: `{wood:200}`
   - L→4: `{wood:400}`
   - L→5: `{wood:500, stone:200}`
   - L→6: `{wood:600, stone:400}`
   - L→7: `{wood:700, stone:600, iron:300}`
   - L→10: `{wood:1000, stone:1200, iron:1200}`
   - L→11: raises `ValueError` (over cap)
  Tests must FAIL.
- [x] **T19**: Implement `src/game/buildings/costs.py` (`build_cost`, `upgrade_cost`). Run tests — must PASS.
- [x] **T20**: Write `tests/test_buildings.py` covering each subclass: type tag, footprint (2×2 for resource, 3×3 for TownHall), `income(level)` = `5×level` of correct resource, TownHall income empty, level cap enforcement. Tests must FAIL.
- [x] **T21**: Implement `src/game/buildings/base.py` + `town_hall.py`, `lumber_camp.py`, `stone_mine.py`, `iron_mine.py`, `farm.py`. Run tests — must PASS.
- [x] **T22**: Write `tests/test_registry.py` covering: cannot place outside grass; cannot overlap; distance rule rejects placement closer than ceil(0.5×max_dim) tiles; second TownHall rejected; `demolish` clears occupancy. Tests must FAIL.
- [x] **T23**: Implement `src/game/buildings/registry.py` (`BuildingRegistry` with `can_place`, `place`, `demolish`, `at`, `all`). Run tests — must PASS.
- [x] **T24**: Implement `src/game/ui/bottom_bar.py` — 96 px strip with 4 build buttons (Lumber, Stone, Iron, Farm) showing icon + name + "100🪵". Greyed when insufficient wood. Click → emits selection event.
- [x] **T25**: Implement `src/game/ui/placement.py` — placement controller: snaps mouse to grid, draws translucent contour green/red, left-click places (delegates to registry, deducts wood), right-click/Esc cancels.

### Phase 5 — Building Panel & Actions

- [x] **T26**: Implement `src/game/ui/building_panel.py` — modal panel: name, level, description, income, worker status, Upgrade button (with cost), Demolish button, [×] close. Layout per PRD §3 F-UI-PANEL. Manual smoke check.
- [x] **T27**: Implement click-on-building → opens BuildingPanel; clicking outside or [×] closes it. Wire into `input.py`.
- [x] **T28**: Implement Upgrade action: deducts `upgrade_cost(level)`, increments level, recomputes `per_cycle` income. Disabled at level 10 or insufficient resources. Add a regression test in `test_buildings.py`.
- [x] **T29**: Implement Demolish action: removes building from registry, sets any worker to idle and parks them on the former center tile. Add regression test in `test_registry.py` and `test_workers.py`.
- [ ] **T30**: Implement `src/game/ui/town_hall_panel.py` extending BuildingPanel: hide Upgrade and Demolish, show "Hire Workers" section with one button per worker type costing 50 food. Disabled when food < 50.

### Phase 6 — Workers

- [ ] **T31**: Write `tests/test_workers.py` covering: `hire` deducts 50 food and returns Worker; `hire` returns None when insufficient food and does not deduct; `reassign_all` matches one idle worker per free building of correct type; type mismatch never assigned; demolition leaves worker on tile and idle; subsequent reassignment moves them when a slot opens. Tests must FAIL.
- [ ] **T32**: Implement `src/game/workers.py` (`Worker`, `WorkerManager` with `hire`, `reassign_all`, `idle`). Run tests — must PASS.
- [ ] **T33**: Wire WorkerManager into game state: every place/demolish/hire/upgrade calls `reassign_all()`; hire button in town hall panel calls `WorkerManager.hire(type)`.
- [ ] **T34**: Render workers on screen: assigned workers as a colored dot at building center; idle workers stacked next to Town Hall; demolition-orphaned workers at the former center tile (until reassigned).
- [ ] **T35**: Update Top Bar's `+income` to reflect current production (sum of `5×level` over buildings with workers). Add regression test in `test_production.py` (placeholder file).
- [ ] **T36**: Manual integration check: launch game, build a Lumber Camp, hire a Lumberjack from Town Hall, observe assignment and visual placement.

### Phase 7 — Production, Polish, Package

- [ ] **T37**: Write `tests/test_production.py` end-to-end (no display): create World+Registry+WorkerManager+ResourceManager, place Lumber Camp + hire+assign a worker, fire one tick → wood increased by 5; upgrade to L3 → next tick adds 15. Tests must FAIL initially.
- [ ] **T38**: Implement production loop in `main.py` (or `game/loop.py`): on tick, sum `5×level` per building with worker → `resources.add(...)`. Run tests — must PASS.
- [ ] **T39**: Verify clean shutdown: in `main.py` ensure `pygame.quit()` runs in a `finally:` block; no daemon threads are spawned (or all are joined). Add `tests/test_shutdown.py` that imports main, runs `main()` in a thread for 1 s with QUIT event injected, and asserts the thread exits within 2 s.
- [ ] **T40**: Polish — verify FPS counter (debug-only) stays ≥55 with 50 buildings + 50 workers in a stress fixture. Optional perf sanity test.
- [ ] **T41**: Add `game.spec` and `build_exe.bat` for PyInstaller (`pyinstaller --onefile --noconsole -n IsometricStrategy src/game/main.py`). Document the command in `README.md`. Smoke check: `dir build_exe.bat` (no actual exe build required in CI).
- [ ] **T42**: Final `README.md`: how to run from source (`pip install -r requirements.txt && python -m game.main`), how to build the exe (`build_exe.bat`), controls (LMB place / open panel, RMB or Esc cancel), gameplay summary. Output `<promise>ALL_TASKS_COMPLETE</promise>` after committing.

---

## Decisions Log

| Date | Task | Decision | Rationale |
|------|------|----------|-----------|
|      |      |          |           |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
|      |      |       |        |

## Notes

- Ambiguity in user spec: per-cycle stone/iron upgrade increment was not stated explicitly for level 5 vs subsequent levels. We follow the wood pattern: stone +200/level from L5, iron +300/level from L7 (see PRD §3 F-BLD-05). Record any alternative in the Decisions Log if changed.
- Worker hire cost not stated by user → fixed at 50 food. Any change → Decisions Log.
- Workers teleport (no pathfinding) — keeps scope small and deterministic.
- All assets are procedural; no binary files in the repo.
- Tests run headless via `SDL_VIDEODRIVER=dummy` set in `tests/conftest.py`.
