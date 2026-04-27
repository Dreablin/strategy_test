# Progress Archive — Phases 1–10

This archive holds the original detailed task lists for completed phases. The
live task tracker (`progress.md`) keeps only the current phase plus the
immediately preceding one (Phase 11) for ralph-loop input context.

All tasks below are `[x]` complete and documented here for traceability only —
ralph-loop must NOT re-run them. New work belongs to a fresh phase in
`progress.md`.

---

## Phase 1 — Project Foundation

- [x] **T01**: Create project skeleton — `src/game/`, `tests/`, `requirements.txt` (pygame 2.5.2, pytest 8.3.3, pyinstaller 6.10.0, ruff 0.6.9), `pyproject.toml`, `.gitignore`, empty `README.md`, empty `src/game/__init__.py`, `tests/__init__.py`. Verify `pip install -r requirements.txt` and `pytest -q` (0 tests, exits 0).
- [x] **T02**: Write `tests/conftest.py` setting `os.environ["SDL_VIDEODRIVER"]="dummy"` BEFORE any pygame import; autouse fixture init/quit pygame per session.
- [x] **T03**: Write `tests/test_config.py` asserting required constants (`TICK_MS=10_000`, `TILE_W=64`, `TILE_H=32`, `GRID_SIZE=32`, `INITIAL_RESOURCES=...`, etc.).
- [x] **T04**: Implement `src/game/config.py`.
- [x] **T05**: Write `tests/test_iso.py` covering round-trips for `world_to_screen`/`screen_to_world`.
- [x] **T06**: Implement `src/game/iso.py` with classic 2:1 isometric transform.
- [x] **T07**: Implement `src/game/main.py` (1280×720 pygame window, 60 FPS loop, clean shutdown).

## Phase 2 — Resources & Top Bar

- [x] **T08**: Write `tests/test_resources.py` (initial values, add, has, try_spend).
- [x] **T09**: Implement `ResourceManager` in `src/game/resources.py`.
- [x] **T10**: Write `tests/test_tick.py` covering 10 s tick boundary.
- [x] **T11**: Implement `TickScheduler` in `src/game/tick.py`.
- [x] **T12**: Implement `src/game/assets.py` (procedural sprite/icon factory, cached).
- [x] **T13**: Implement `src/game/ui/top_bar.py` (48 px strip with 4 resource entries).

## Phase 3 — World & Rendering

- [x] **T14**: `tests/test_world.py` — grid, occupancy, grass/tree zones.
- [x] **T15**: Implement `src/game/world.py` (`World` with grid + occupancy bitmap + grass/tree zones).
- [x] **T16**: Implement `src/game/render.py` `Renderer.draw_world` (grass diamonds + tree borders).
- [x] **T17**: Wire `World` + `Renderer` into `main.py`.

## Phase 4 — Buildings & Placement

- [x] **T18**: `tests/test_costs.py` covering `upgrade_cost(L)` for L=1..10 with stone@5+, iron@7+.
- [x] **T19**: Implement `src/game/buildings/costs.py`.
- [x] **T20**: `tests/test_buildings.py` per subclass (type, footprint, income, level cap).
- [x] **T21**: Implement `Building`, `TownHall`, `LumberCamp`, `StoneMine`, `IronMine`, `Farm`.
- [x] **T22**: `tests/test_registry.py` (placement validity, distance rule, second TH rejected).
- [x] **T23**: Implement `BuildingRegistry`.
- [x] **T24**: Implement `src/game/ui/bottom_bar.py` (4 build buttons, greyed when poor).
- [x] **T25**: Implement `src/game/ui/placement.py` (mouse-follow contour, click to place).

## Phase 5 — Building Panel & Actions

- [x] **T26**: Implement `BuildingPanel` (modal: name, level, description, income, status, actions, [×]).
- [x] **T27**: Wire click-on-building to open `BuildingPanel`; outside/[×] closes.
- [x] **T28**: Implement Upgrade action.
- [x] **T29**: Implement Demolish action (worker idle + parked at former center).
- [x] **T30**: Implement `TownHallPanel` (no demolish, hire buttons per worker type).

## Phase 6 — Workers

- [x] **T31**: `tests/test_workers.py` (hire deducts food, idle queue, type-matched assignment, demolition).
- [x] **T32**: Implement `Worker`, `WorkerManager` (hire, reassign_all, idle).
- [x] **T33**: Wire WorkerManager into game state.
- [x] **T34**: Render workers on screen (assigned dot, idle stack, orphans).
- [x] **T35**: Update Top Bar `+income`.
- [x] **T36**: Manual integration check.

## Phase 7 — Production, Polish, Package

- [x] **T37**: `tests/test_production.py` end-to-end.
- [x] **T38**: Implement production loop in `main.py` (or `game/loop.py`).
- [x] **T39**: Verify clean shutdown; `tests/test_shutdown.py`.
- [x] **T40**: Polish — FPS counter ≥ 55 with 50 buildings + 50 workers.
- [x] **T41**: `game.spec` + `build_exe.bat` for PyInstaller.
- [x] **T42**: Final `README.md`.

## Phase 8 — Render Fixes & Camera Pan

> Bugs A/B (Town Hall + new buildings invisible) + RMB drag camera.

- [x] **T43–T44**: `Renderer.draw_buildings` regression tests + implementation; wired into `main.py`.
- [x] **T45–T46**: `tests/test_camera.py` + `Camera` class with pan/clamp.
- [x] **T47**: Camera-aware rendering for world/buildings/workers/placement.
- [x] **T48**: `screen_to_grid` takes a `Camera`; tests for offset round-trip.
- [x] **T49**: RMB drag pan with 4 px threshold (`tests/test_rmb_drag.py`).
- [x] **T50**: World pixel bounds for clamping (`tests/test_world_bounds.py`).
- [x] **T51**: Smoke integration `tests/test_smoke_phase8.py`.

## Phase 9 — Worker Movement & Building Spacing

> 1 tile / 3 s walking; no stepping on buildings; 1-tile gap between footprints.

- [x] **T52–T53**: Spacing rule (Chebyshev ≥ 1) in registry.
- [x] **T54–T55**: `tests/test_worker_movement.py` + `Worker.update`/path queue.
- [x] **T56–T57**: `tests/test_pathfinding.py` + BFS in `src/game/pathfinding.py` (8-dir, no corner cutting, deterministic).
- [x] **T58**: Approach-tile selection in `WorkerManager.reassign_all`.
- [x] **T59**: Production gating via `working_buildings()`; demolition orphans worker.
- [x] **T60**: Smooth worker rendering (interpolated position).
- [x] **T61**: Wire `worker_manager.update(now_ms)` into `main.py`.
- [x] **T62**: `tests/test_smoke_phase9.py` end-to-end.

## Phase 10 — Tree Entities, Placement Clearing & Render Layering

> Trees become world-owned entities with growth stages; chopping is a future flow.

- [x] **T63–T64**: `tests/test_trees.py` + `src/game/trees.py` (`TreeStage`, `Tree`).
- [x] **T65–T66**: World owns trees by tile; edge-biased generation, center clearing.
- [x] **T67–T68**: BFS treats alive tree tiles as blocked; movement detours.
- [x] **T69–T70**: Placement clears trees inside the new footprint.
- [x] **T71–T72**: Tree assets per stage; loader with procedural fallback.
- [x] **T73–T74**: Render layering — trees draw above buildings/workers behind them.

---

## Decisions kept from old log

- Stone +200/level from L5, iron +300/level from L7 mirror the wood pattern.
- Worker hire cost fixed at 50 food (later moved to `game_settings.json` and reduced to 5).
- All assets are procedural fallback; binary placeholders OK once `asset_meta.json` carries scale/anchor.
- Tests run headless via `SDL_VIDEODRIVER=dummy`.
