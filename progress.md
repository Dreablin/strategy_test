# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 8. Render fixes & camera pan
- **Next Task:** T49 — Implement RMB drag pan behavior
- **Last Completed:** T48 — Camera-aware input grid conversion
- **Total Progress:** 48 / 51

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
- [x] **T30**: Implement `src/game/ui/town_hall_panel.py` extending BuildingPanel: hide Upgrade and Demolish, show "Hire Workers" section with one button per worker type costing 50 food. Disabled when food < 50.

### Phase 6 — Workers

- [x] **T31**: Write `tests/test_workers.py` covering: `hire` deducts 50 food and returns Worker; `hire` returns None when insufficient food and does not deduct; `reassign_all` matches one idle worker per free building of correct type; type mismatch never assigned; demolition leaves worker on tile and idle; subsequent reassignment moves them when a slot opens. Tests must FAIL.
- [x] **T32**: Implement `src/game/workers.py` (`Worker`, `WorkerManager` with `hire`, `reassign_all`, `idle`). Run tests — must PASS.
- [x] **T33**: Wire WorkerManager into game state: every place/demolish/hire/upgrade calls `reassign_all()`; hire button in town hall panel calls `WorkerManager.hire(type)`.
- [x] **T34**: Render workers on screen: assigned workers as a colored dot at building center; idle workers stacked next to Town Hall; demolition-orphaned workers at the former center tile (until reassigned).
- [x] **T35**: Update Top Bar's `+income` to reflect current production (sum of `5×level` over buildings with workers). Add regression test in `test_production.py` (placeholder file).
- [x] **T36**: Manual integration check: launch game, build a Lumber Camp, hire a Lumberjack from Town Hall, observe assignment and visual placement.

### Phase 7 — Production, Polish, Package

- [x] **T37**: Write `tests/test_production.py` end-to-end (no display): create World+Registry+WorkerManager+ResourceManager, place Lumber Camp + hire+assign a worker, fire one tick → wood increased by 5; upgrade to L3 → next tick adds 15. Tests must FAIL initially.
- [x] **T38**: Implement production loop in `main.py` (or `game/loop.py`): on tick, sum `5×level` per building with worker → `resources.add(...)`. Run tests — must PASS.
- [x] **T39**: Verify clean shutdown: in `main.py` ensure `pygame.quit()` runs in a `finally:` block; no daemon threads are spawned (or all are joined). Add `tests/test_shutdown.py` that imports main, runs `main()` in a thread for 1 s with QUIT event injected, and asserts the thread exits within 2 s.
- [x] **T40**: Polish — verify FPS counter (debug-only) stays ≥55 with 50 buildings + 50 workers in a stress fixture. Optional perf sanity test.
- [x] **T41**: Add `game.spec` and `build_exe.bat` for PyInstaller (`pyinstaller --onefile --noconsole -n IsometricStrategy src/game/main.py`). Document the command in `README.md`. Smoke check: `dir build_exe.bat` (no actual exe build required in CI).
- [x] **T42**: Final `README.md`: how to run from source (`pip install -r requirements.txt && python -m game.main`), how to build the exe (`build_exe.bat`), controls (LMB place / open panel, RMB or Esc cancel), gameplay summary. Output `<promise>ALL_TASKS_COMPLETE</promise>` after committing.

### Phase 8 — Render Fixes & Camera Pan

> **Context for this phase:** play-testing exposed two critical render bugs and one missing feature. PRD has been updated by the user (sections F-ISO-01, F-INPUT, F-CAM, F-RENDER, API §6 additions). Do NOT edit PRD; just satisfy the new requirements.
>
> - Bug A: the Town Hall is never drawn at startup.
> - Bug B: a freshly placed building is invisible too (resources are deducted, registry contains it, clicking its tile opens the info panel — only the sprite is missing).
> - Feature: pan the camera by holding RMB and dragging, with bounds clamped to the world's bounding rectangle.
> - Root cause for A & B: `Renderer` has no `draw_buildings` method and `main.py`'s render pipeline never calls one.

- [x] **T43**: Write `tests/test_render_buildings.py` with these tests (must FAIL because `Renderer.draw_buildings` does not exist yet):
   1. `test_draw_buildings_attribute` — `getattr(Renderer, "draw_buildings", None)` is callable.
   2. `test_initial_town_hall_drawn` — create `World()` + `BuildingRegistry(world)` + `ResourceManager()` exactly as `main.py` does (initial state must include the Town Hall at the centre tile, per PRD F-WORLD-03). Create a 1280×720 surface, fill with sentinel colour `(20, 24, 22)`, call `Renderer.draw_world(surface, world)` then `Renderer.draw_buildings(surface, world, registry)`. Sample the pixel at the screen position of the Town Hall's footprint centre and assert it is **not** the sentinel colour and **not** the grass colour — i.e., something building-coloured was blitted there.
   3. `test_placed_building_drawn` — same setup, then place a `LumberCamp` at a valid tile via `registry.place(...)` and re-render. Sample the placed building's centre pixel — must be different from grass / sentinel.
   4. `test_painters_order` — record `surface.blit` calls (use a thin spy `class _Spy(pygame.Surface): def blit(self, *a, **kw): self.calls.append((a, kw)); return super().blit(*a, **kw)`). Place two buildings at `(8, 8)` and `(20, 20)`. Assert the call for `(8, 8)` precedes the call for `(20, 20)` (lower `gx+gy` drawn first).

- [x] **T44**: Implement `Renderer.draw_buildings(surface, world, registry, camera=None)`:
   - Iterate `registry.all()`, sort by `(b.grid_pos[0] + b.grid_pos[1], b.grid_pos[0])`.
   - For each building, compute footprint screen rect via `iso.world_to_screen` for each footprint tile + `Renderer.map_origin`. Anchor sprite bottom-centre to footprint bottom-centre. Apply `camera.offset` if given (else `(0,0)`).
   - Blit `assets.building_sprite(b.type_tag, b.level)`.
   - Wire into `src/game/main.py` between `Renderer.draw_world(...)` and `Renderer.draw_workers(...)`.
   - Run `pytest -q` — T43 tests now PASS, full suite stays green.

- [x] **T45**: Write `tests/test_camera.py` (must FAIL — `game.camera` does not exist):
   - `test_initial_offset` — `Camera()` has `offset == (0, 0)`.
   - `test_pan_accumulates` — `c.pan(10, 5); c.pan(-3, 1)` ⇒ `c.offset == (7, 6)`.
   - `test_clamp_world_smaller_than_viewport` — viewport `(1280, 720)`, world bounds `(0, 0, 800, 600)`. After `c.pan(50, 50); c.clamp(viewport, bounds)` the offset is locked at the centring value (the value that places the world's centre at the viewport's centre). Pan in any direction is undone by `clamp`.
   - `test_clamp_world_larger_than_viewport` — viewport `(800, 600)`, world bounds `(0, 0, 2000, 2000)`. `c.pan(10000, 10000); c.clamp(...)` constrains offset so the world's max edge cannot move left of the viewport's right edge (and similarly for the other three sides). Pan-and-clamp moving in the opposite direction also stays bounded.

- [x] **T46**: Implement `src/game/camera.py` with the `Camera` class per PRD §6 API and F-CAM-01..05. Run T45 — must PASS.

- [x] **T47**: Refactor rendering to be camera-aware:
   - Add an optional `camera: Camera | None` parameter to `Renderer.draw_world`, `draw_buildings`, `draw_workers`, and `PlacementController.draw`.
   - When a camera is provided, add `camera.offset[0]` to every blit's `x` and `camera.offset[1]` to every blit's `y`.
   - `TopBar`, `BottomBar`, `BuildingPanel`, `TownHallPanel` MUST NOT be camera-shifted — they stay anchored to the screen.
   - In `main.py`, instantiate one `Camera()`, pass it through the render calls.
   - Update existing tests to pass `camera=None` where appropriate; add a regression test in `test_render_buildings.py` asserting that with `Camera(offset=(50, 30))` the building's drawn pixel position is shifted by `(50, 30)`.
   - `pytest -q` — full suite green.

- [x] **T48**: Refactor `screen_to_grid` in `src/game/input.py` to take a `Camera`:
   - Signature: `screen_to_grid(surface, world, screen_pos, camera)`.
   - Subtracts `camera.offset` before subtracting `Renderer.map_origin` and calling `iso.screen_to_world`.
   - Update all call sites: `GameInput._handle_map_left_click`, `PlacementController.update_hover`, `try_place`. Pass `camera` from `main.py` into `GameInput` and `PlacementController` constructors.
   - Add `tests/test_input_camera.py`: with `Camera(offset=(64, 32))`, a screen click at the previously-correct coords for tile `(5, 5)` shifted by `(64, 32)` round-trips back to grid `(5, 5)`.
   - `pytest -q` — green.

- [ ] **T49**: Implement RMB drag pan in `GameInput`:
   - State: `_rmb_down: bool`, `_rmb_press_pos: (int, int)`, `_rmb_dragging: bool`.
   - `MOUSEBUTTONDOWN button=RIGHT`: store press pos, `_rmb_down=True`, `_rmb_dragging=False`. Do NOT cancel placement yet.
   - `MOUSEMOTION` while `_rmb_down`: if Chebyshev distance from `_rmb_press_pos` ≥ 4 px, set `_rmb_dragging=True` and call `camera.pan(event.rel[0], event.rel[1])` then `camera.clamp(viewport, world_bounds)`.
   - `MOUSEBUTTONUP button=RIGHT`: if `_rmb_dragging` is False → existing cancel behaviour (close panel, cancel placement). Else swallow. Reset state.
   - Add `tests/test_rmb_drag.py` exercising the threshold logic with stub events and a stub camera (no display): drag of 3 px → cancel; drag of 5 px → pan called once and no cancel.
   - `pytest -q` — green.

- [ ] **T50**: Compute world bounds for clamping in `main.py`:
   - World pixel bounds = the bounding rect of all (grass + tree-skirt) tiles per `Renderer._compute_grass_origin` math, expressed as `(min_x, min_y, max_x, max_y)` *before* `map_origin` re-centring. Provide a helper `Renderer.world_pixel_bounds(world) -> tuple[int,int,int,int]` so the camera's `clamp` can be called consistently.
   - Compute viewport play-area size = `(WINDOW_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT)`.
   - In the main loop after every pan: `camera.clamp(play_area_size, Renderer.world_pixel_bounds(world))`.
   - Add `tests/test_world_bounds.py` — bounds returned for the default 32×32 world include the `_TREE_RING_TILES` skirt on every side.
   - `pytest -q` — green.

- [ ] **T51**: Smoke integration test `tests/test_smoke_phase8.py` (uses `SDL_VIDEODRIVER=dummy`):
   1. Boot world+registry+resources+worker_manager+placement+input+camera as `main.py` does.
   2. Render one frame onto the screen surface — Town Hall pixel is non-sentinel (verifies bug A fixed).
   3. Inject `BUILD_MENU_SELECT` for `LUMBER_CAMP`, then a synthetic `MOUSEBUTTONDOWN` at a valid placement screen coord, then a `MOUSEBUTTONUP`. Render again — Lumber Camp pixel is non-sentinel (verifies bug B fixed).
   4. Inject `MOUSEBUTTONDOWN` RMB → 3× `MOUSEMOTION` of `(20, 0)` rel → `MOUSEBUTTONUP` RMB. Assert `camera.offset[0] >= 60` (rounded for clamp). Render does not raise.
   5. After tests pass, write `<promise>ALL_TASKS_COMPLETE</promise>` per `prompt.md` step 6 (and create `.cursor/ralph/done`).

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
