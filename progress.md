# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 12. Level bonuses, internal storage, stones
- **Next Task:** T97 — Apply move-speed multiplier in `Worker.update`
- **Last Completed:** T96 — Add failing tests for movement-speed application
- **Total Progress:** 96 / 111

> Phases 1–10 are summarised in `progress_archive.md`. Phase 11 stays here for
> ralph-loop input context (it is the immediate precursor to Phase 12). When
> Phase 12 is complete, archive Phase 11 too.

---

## Hot-Fixes (outside the ralph queue)

### HF12-A — Lumber Camp disappears when player clicks Upgrade (FIXED)

- **Symptom:** clicking the Upgrade button on a `LumberCamp` panel sometimes
  demolished the camp instead of upgrading it.
- **Root cause:** `LumberCampPanel.click_action` resolved hit-targets by calling
  `BuildingPanel.click_action` **twice** — first without `extra_bottom_px=72`
  (legacy frame) and then with it. The drawn panel uses `extra_bottom_px=72`,
  so the legacy frame's `Demolish` rect overlapped the visible `Upgrade`
  button by ~28 px. Lower-half clicks on `Upgrade` matched that legacy
  `Demolish` rect first, returning `"demolish"`.
- **Fix:** keep only the `extra_bottom_px=72` resolution; fall back to the
  `toggle_active` rect last. See
  [`src/game/ui/lumber_camp_panel.py`](src/game/ui/lumber_camp_panel.py).
- **Regression tests:** `tests/test_lumber_camp_panel.py::test_lumber_camp_click_upgrade_returns_upgrade_not_demolish`,
  `…::test_lumber_camp_click_demolish_still_returns_demolish`.
- **Status:** committed; full suite green (221 tests).

---

## Task Log

### Phase 11 — Lumberjack Chop Cycle (DONE — kept for ralph context)

> Lumber Camp no longer passively produces wood. A staffed Lumber Camp dispatches
> its Lumberjack on a chop cycle: walk to a free tree → adjacent free tile →
> chop for 10 s → carry wood back to the camp → deposit `+1 wood` and remove the
> tree. Active/Inactive toggle on the camp; `delivered_wood` counter; `carrying`
> flag on the worker. Two distinct lumberjack sprites (empty / carrying).
> Lumberjack rests inside the camp for `LUMBERJACK_REST_MS = 5000 ms` between
> trips and stays parked inside if the camp is toggled off.

- [x] **T75–T91** (see commit history; full test coverage in
  `tests/test_lumber_camp_state.py`, `test_lumberjack_cycle_states.py`,
  `test_lumber_camp_active_toggle.py`, `test_smoke_phase11.py`, etc.).

---

### Phase 12 — Level Bonuses, Internal Storage, Stones

> **Scope added by user (April 2026):**
>
> 1. **Bug** *(fixed in HF12-A above; do not re-do)*: Lumber Camp disappears on level-up.
> 2. **Rework upgrade reward.** Each level above 1 grants the building's
>    *currently assigned* worker **+5 % move speed AND +5 % gather speed**,
>    additive in fixed-point form (e.g. L5 ⇒ +20 %). The old `5 × level`
>    passive income is gone for `LUMBER_CAMP` and `STONE_MINE`. `FARM` and
>    `IRON_MINE` keep passive income for now (rewrite is out of scope for
>    Phase 12) but get the storage cap.
> 3. **Worker characteristics + bonuses.** Each worker has a `Characteristics`
>    block (movement / gather speed multipliers) and a list of bonus sources
>    (permanent / temporary). Permanent bonuses are tied to a "source" key so
>    they can be added/removed atomically (e.g. `("building_level", camp_id)`).
> 4. **Internal storage.** Producing buildings now hold a typed stack of units
>    `stored / capacity(L)`, where `capacity(L) = 3 + 2 × (L − 1)`. A new
>    cycle / tick is **gated** when storage is full. Future phases will pick
>    up resources from buildings; this phase only fills them.
> 5. **Stones on the map.** New world entity `Stone(units=15)`. Generation:
>    3 random centres at Chebyshev ≥ 12 from the Town Hall, each with a random
>    radius `r ∈ [3, 6]` filled with stones. Stones block movement and
>    placement, never share a tile with a tree. Stonecutter gather logic
>    mirrors lumberjack: walk to stone → mine 1 unit → return to camp →
>    deposit `+1 stone`. Stones decrement by 1 per harvest; tile reverts to
>    plain grass at 0 units.
> 6. **STONE_MINE active cycle.** Same state machine as `LumberCamp`
>    (active toggle, delivered counter, carrying sprite). MINER and FARMER
>    stay passive in this phase.
>
> Constants / keys (suggested):
>
> - `MOVE_SPEED_PER_LEVEL = 0.05`
> - `GATHER_SPEED_PER_LEVEL = 0.05`
> - `MINE_DURATION_MS = 10_000`
> - `STONECUTTER_REST_MS = 5_000`
> - `STONE_UNITS_PER_TILE = 15`
> - `STONE_GEN_CENTERS = 3`
> - `STONE_MIN_DISTANCE_FROM_TOWN_HALL = 12`
> - `STONE_RADIUS_RANGE = (3, 6)`
> - `BUILDING_STORAGE_BASE = 3`
> - `BUILDING_STORAGE_PER_LEVEL = 2`
> - `STONE_RESOURCE_KEY = "stone"`
> - `STONE_ASSET_DIR = "assets/world/stone/"`
> - Worker bonus source keys: `("building_level", id(building))`.

#### 12.1 Worker characteristics & permanent bonuses

- [x] **T92**: Add failing tests for the worker characteristics module in new
  `tests/test_worker_characteristics.py`:
  - `Characteristics()` defaults: `move_speed_mult == 1.0`,
    `gather_speed_mult == 1.0`.
  - `Characteristics.add_permanent(source, kind, value)` increments the
    matching multiplier; `kind ∈ {"move_speed_mult", "gather_speed_mult"}`,
    `value` is the additive delta (e.g. 0.05 for +5 %). Adding under the same
    `(source, kind)` key replaces the previous value (no double-stacking).
  - `Characteristics.remove_source(source)` undoes all bonuses keyed by
    `source`.
  - `Characteristics.add_temporary(kind, value, expires_at_ms)` adds a
    timed delta. `tick(now_ms)` removes any temporary bonus whose
    `expires_at_ms <= now_ms`.
  - Effective multipliers are clamped to a positive minimum (e.g. `0.10`)
    so workers never freeze.
  Tests must FAIL first.

- [x] **T93**: Implement `src/game/characteristics.py`:
  - `Characteristics` class with two derived multipliers and an internal
    `dict[(source_key, kind), float]` of permanent deltas plus a list of
    `(kind, value, expires_at_ms)` for temporaries.
  - `tick(now_ms)` purges expired temporaries.
  - Use `__slots__`; no Pygame dependency. Run `pytest -q
    tests/test_worker_characteristics.py` — PASS.

- [x] **T94**: Add failing tests for `Worker` integration in
  `tests/test_workers.py`:
  - New attribute `worker.characteristics` is a `Characteristics`.
  - Newly hired worker has `move_speed_mult == 1.0`,
    `gather_speed_mult == 1.0`.
  - `WorkerManager.notify_demolished(building)` clears any
    `("building_level", id(building))` source from the worker.
  - Reassigning a worker to a different building swaps the source.
  Tests must FAIL first.

- [x] **T95**: Wire `Characteristics` into `Worker` (`src/game/workers.py`):
  - Extend `__slots__`, initialise in `__init__`.
  - On `assign_to_building` / `reassign_all` success: call
    `worker.characteristics.remove_source(("building_level", id(prev_camp)))`,
    then `add_permanent(("building_level", id(new_camp)),
    "move_speed_mult", (new_camp.level − 1) * MOVE_SPEED_PER_LEVEL)` and
    similarly for `gather_speed_mult`.
  - On demolition / become-idle: remove the source.
  - On building upgrade (next task) the registry/UI dispatches
    `worker_manager.refresh_worker_bonuses()` to re-apply new deltas.
  - Run `pytest -q` — green.

#### 12.2 Apply level bonuses to movement and gather speed

- [x] **T96**: Add failing tests for movement-speed application in
  `tests/test_worker_movement.py`:
  - With `move_speed_mult == 1.0`, traversing one tile takes
    `WORKER_TILE_TRAVEL_MS` (already covered).
  - With `move_speed_mult == 1.20`, traversal completes after
    `WORKER_TILE_TRAVEL_MS / 1.20` ms (rounded to int ms with deterministic
    tolerance ≤ 1 ms).
  - Multiple-tile path interpolation respects the same effective duration
    per tile.
  Tests must FAIL first.

- [ ] **T97**: Update `Worker.update(now_ms)` (`src/game/workers.py`) to use the
  effective per-tile duration:
  - `effective_travel_ms = max(1, int(round(WORKER_TILE_TRAVEL_MS /
    self.characteristics.move_speed_mult)))`.
  - Replace the current hard-coded `WORKER_TILE_TRAVEL_MS` boundaries.
  - Add a fast helper for tests if needed (`Worker._effective_travel_ms()`).
  - Run movement tests — green.

- [ ] **T98**: Add failing tests for chop / mine duration scaling in
  `tests/test_lumberjack_cycle_chopping.py` and a new
  `tests/test_lumberjack_speed_bonus.py`:
  - With camp at level 1 (no bonus) chop completes after
    `CHOP_DURATION_MS`.
  - With camp at level 5 the chop completes after `CHOP_DURATION_MS / 1.20`
    ms (assert exact integer ms after applying the same rounding rule as
    movement).
  - Demolish-during-chop still cancels deterministically.
  Tests must FAIL first.

- [ ] **T99**: Update `WorkerManager.update` chop cycle:
  - Compute `effective_chop_ms = max(1, int(round(CHOP_DURATION_MS /
    worker.characteristics.gather_speed_mult)))` at chop start (snapshot,
    not re-read mid-chop).
  - Use that snapshot for the `now_ms - chop_started_ms >= …` check.
  - Run all lumberjack tests — green.

- [ ] **T100**: Add failing tests for `BuildingRegistry.upgrade_building`
  side-effects in `tests/test_registry.py`:
  - Upgrading a camp keeps the building in the registry (regression for
    HF12-A; assert `camp in registry.all()` after upgrade).
  - The assigned worker's `gather_speed_mult` increases by exactly
    `MOVE_SPEED_PER_LEVEL` after a 1→2 upgrade.
  - Multiple consecutive upgrades stack additively, not multiplicatively.
  - Demolish removes both bonus sources (move + gather) from the worker.
  Tests must FAIL first.

- [ ] **T101**: Implement registry → worker bonus refresh:
  - In `BuildingRegistry.upgrade_building`, after `building.level += 1`,
    notify the `WorkerManager` (inject reference, or callback). The manager
    finds the staffed worker (if any) and calls
    `characteristics.remove_source(...)` then re-adds with the new level
    delta.
  - Add a `WorkerManager.refresh_building_bonuses(building)` helper.
  - Run all tests — green; HF12-A regression case is now in CI.

#### 12.3 Internal storage on producing buildings

- [ ] **T102**: Add failing tests for storage in
  `tests/test_buildings.py`:
  - Each of `LumberCamp`, `StoneMine`, `IronMine`, `Farm` has fields
    `stored: int = 0` and method `storage_capacity()` returning
    `BUILDING_STORAGE_BASE + BUILDING_STORAGE_PER_LEVEL × (level − 1)`.
  - `add_to_storage(n)` raises if `n < 0` or would overflow capacity.
  - `take_from_storage(n)` raises if `n` exceeds `stored`.
  - `is_storage_full()` returns True iff `stored == capacity`.
  - `TownHall` does NOT expose any of these (assert `AttributeError` /
    method missing).
  Tests must FAIL first.

- [ ] **T103**: Add a mixin / base storage helper used by the four producing
  buildings:
  - Recommend `src/game/buildings/storage.py` exposing a small mixin or a
    helper class that stores `stored: int` plus `storage_capacity(level)`
    static method. Apply to `LumberCamp`, `StoneMine`, `IronMine`, `Farm`.
  - Update `__slots__`. Run `pytest -q tests/test_buildings.py` — green.

- [ ] **T104**: Add failing tests for production gating by storage in
  `tests/test_lumberjack_cycle_deposit.py` and
  `tests/test_production.py`:
  - Once `LumberCamp.stored == LumberCamp.storage_capacity()`, the next
    chop cycle does NOT start (worker stays inside camp; deposit count
    does not grow until storage drops).
  - Per-tick passive income for `Farm` and `IronMine` skips when
    `stored >= capacity`.
  Tests must FAIL first.

- [ ] **T105**: Implement storage gating:
  - In `WorkerManager.update`, when a `LUMBERJACK` (resp. `STONECUTTER`)
    is in the `working` rest state and ready to start a new cycle, also
    require `not camp.is_storage_full()`.
  - In `apply_production_tick` (`src/game/loop.py`) and
    `BuildingRegistry.sync_resources_per_cycle`, skip a tick of passive
    income for any producing building whose storage is full.
  - Each successful deposit calls `camp.add_to_storage(1)` in addition to
    `resources.add(...)`.
  - Run all tests — green.

- [ ] **T106**: Add failing UI tests for storage display in
  `tests/test_lumber_camp_panel.py` and a new
  `tests/test_building_panel_storage.py`:
  - The panel renders a `Storage: <stored> / <capacity>` line for each of
    the four producing buildings.
  - Capacity changes immediately on level-up.
  - Tests assert via `LumberCampPanel.storage_line(camp)` /
    `BuildingPanel.storage_line(building)` (or string scrape; pick one).
  Tests must FAIL first.

- [ ] **T107**: Implement storage line rendering in `BuildingPanel.draw` and
  `LumberCampPanel.draw`. Adjust the `extra_bottom_px` accumulator so the
  modal grows by one row, and update `BuildingPanelLayout` if necessary.
  Run UI tests — green.

#### 12.4 Stones on the map

- [ ] **T108**: Add failing tests for the stone domain object in new
  `tests/test_stones.py`:
  - `Stone` model with `units: int = 15`, `harvest()` decrements by 1 and
    returns the new value; `harvest()` raises if `units == 0`.
  - `is_depleted` is True iff `units == 0`.
  - World API: `world.stone_at(gx, gy) -> Stone | None`,
    `world.is_stone_blocking(gx, gy) -> bool`,
    `world.iter_stones() -> list[((gx, gy), Stone)]`,
    `world.harvest_stone(gx, gy) -> Stone | None` (decrements and removes
    when depleted).
  - Reservation API mirrors trees:
    `reserve_stone(gx, gy, worker)`, `release_stone(gx, gy)`,
    `release_reservations_for(worker)` (already exists; extend it).
  Tests must FAIL first.

- [ ] **T109**: Implement `src/game/stones.py` (or a small section in
  `src/game/world.py`) and wire World methods.
  - Use `__slots__`. Keep generation deterministic given a seed.
  - The reservation system is shared with trees; rename internal storage
    to a more generic `_resource_reservations` or keep a parallel dict —
    consistent with existing design.

- [ ] **T110**: Add failing tests for stone generation in
  `tests/test_world.py`:
  - With a fixed seed, exactly 3 generation centres are picked, all in
    grass, all at Chebyshev ≥ 12 from any Town Hall footprint tile.
  - Around each centre, every tile inside `r` (random `r ∈ [3, 6]`) that
    is not a tree, not a building footprint, and inside the grid hosts a
    `Stone(units=15)`.
  - No tile can host both a tree and a stone simultaneously.
  - Stone generation is idempotent: running the seed again from a fresh
    `World()` produces identical output.
  Tests must FAIL first.

- [ ] **T111**: Implement deterministic stone generation in
  `World._init_stones()` (called from `__init__`):
  - Use a stable PRNG derived from a constant seed (or `GRID_SIZE`-based
    seed already used for trees) so tests are reproducible.
  - Skip tiles that are trees or already stones; skip tiles within
    `STONE_MIN_DISTANCE_FROM_TOWN_HALL` of the Town Hall **footprint**
    (ratchet: tests must check this even though the Town Hall is placed
    by the registry, not the world — accept a dependency-injection hook
    `World.set_protected_tiles(set)` if needed).
  - Run `pytest -q tests/test_world.py` — green.

- [ ] **T112**: Add failing tests for movement & placement blocking by stones
  in `tests/test_pathfinding.py`, `tests/test_registry.py`,
  `tests/test_workers.py`:
  - BFS treats alive stone tiles as blocked (no path through).
  - `BuildingRegistry.can_place` returns False when the footprint covers
    any stone tile, even if the spacing rule would otherwise accept it.
  - `BuildingRegistry.place` does NOT remove stones (unlike trees).
  Tests must FAIL first.

- [ ] **T113**: Update pathfinding (`src/game/pathfinding.py`) and registry
  (`src/game/buildings/registry.py`) to treat stones as blockers and
  un-buildable. Run all tests — green.

- [ ] **T114**: Add failing render tests in
  `tests/test_render_stones.py`:
  - World API: `world.iter_stones()` returns all stones.
  - `Renderer.draw_stones(surface, world, camera=None)` (or extension of
    `draw_trees`) blits a stone sprite anchored bottom-centre per stone
    tile, sorted with the same painter key.
  - With `Camera(offset=(50, 30))`, the draw position is shifted.
  - Procedural fallback exists when `assets/world/stone/default.png` is
    missing.
  Tests must FAIL first.

- [ ] **T115**: Add a placeholder asset folder
  `assets/world/stone/default.png` (procedurally generated grey isometric
  pile is acceptable; commit a real placeholder PNG so disk-first loader
  can hot-swap later) plus an `asset_meta.json` mirroring the building
  scheme. Implement `assets.stone_sprite()` with the same mtime hot-reload
  caching used for buildings/trees, and add the `Renderer.draw_stones`
  pass. Run all render tests — green.

#### 12.5 Stonecutter active cycle

- [ ] **T116**: Add failing tests for `StoneMine` state in new
  `tests/test_stone_mine_state.py`:
  - `StoneMine.active: bool = True`, `StoneMine.delivered_stone: int = 0`.
  - `set_active(False/True)` works; `record_stone_delivered(n)` is
    increment-only and rejects negatives.
  - Other building types do NOT expose those fields (negative test).
  Tests must FAIL first.

- [ ] **T117**: Implement Active toggle and counter on `StoneMine`
  (`src/game/buildings/stone_mine.py`) using the same pattern as
  `LumberCamp`. Update `__slots__`. Run those tests — green.

- [ ] **T118**: Add failing tests for the stonecutter state machine in new
  `tests/test_stonecutter_cycle.py`:
  - State transitions for STONECUTTER assigned to an active StoneMine
    mirror lumberjack: `idle → moving → working (rest) → going_to_stone
    → mining → returning → arrived_camp → depositing → working`.
  - `worker.carrying` becomes `"stone"` after a successful mine and is
    cleared on deposit.
  - Reservations are honoured: a second stonecutter cannot claim a stone
    already targeted.
  - Demolishing the mine during any active stage cancels the cycle.
  Tests must FAIL first.

- [ ] **T119**: Implement stonecutter dispatch in `WorkerManager`:
  - Generalise the lumberjack dispatch helpers — extract
    `_start_gather_cycle(worker, camp, *, world_query)` parametrised by
    the resource (tree / stone). Reuse `_park_lumberjack_inside_camp`
    rename → `_park_worker_inside_camp`.
  - Add `find_nearest_free_stone(world, from_tile, …)` mirroring
    `find_nearest_free_tree`.
  - The mining duration uses `MINE_DURATION_MS` and respects
    `gather_speed_mult`.
  - Deposit logic: `+1 stone` to `ResourceManager`,
    `camp.record_stone_delivered(1)`, plus storage gating from §12.3.
  - Run all worker tests — green.

- [ ] **T120**: Add failing UI tests for the StoneMine panel in
  `tests/test_stone_mine_panel.py`:
  - Toggle button (Active/Inactive) returns `"toggle_active"` on click.
  - `Stones delivered: N` line mirrors `mine.delivered_stone`.
  - Storage line `Storage: <stored> / <capacity>` is rendered.
  - LumberCamp / Farm / IronMine do not get the stonecutter-specific
    panel.
  Tests must FAIL first.

- [ ] **T121**: Implement `src/game/ui/stone_mine_panel.py` similarly to
  `LumberCampPanel` and wire it into `GameInput` so clicks on a
  `STONE_MINE` open the new panel; reuse the same `extra_bottom_px`
  pattern correctly (no double-resolution bug — see HF12-A).

#### 12.6 End-to-end smoke + cleanup

- [ ] **T122**: Add failing carrying-sprite tests in `tests/test_assets.py`
  for the stonecutter:
  - `worker_dot("STONECUTTER", carrying=False)` and `(…, carrying=True)`
    return distinct surfaces.
  - Procedural fallback exists for both.
  - Folder layout: `assets/npc/stonecutter/default.png` + `…/carrying.png`.
  Tests must FAIL first.

- [ ] **T123**: Implement carrying-sprite loading for stonecutter (same
  contract as lumberjack). Update `Renderer.draw_workers` to dispatch the
  carrying variant when `worker.carrying == "stone"`. Run render tests —
  green.

- [ ] **T124**: End-to-end smoke `tests/test_smoke_phase12.py`
  (`SDL_VIDEODRIVER=dummy`):
  1. World boots with 3 stone clusters, all ≥ 12 tiles from the Town Hall.
  2. Build a Stone Mine adjacent to a stone cluster; placement on stone
     tiles is rejected.
  3. Hire a stonecutter; assert it walks to the mine, rests, then dispatches
     to a stone, mines `MINE_DURATION_MS`, and deposits `+1 stone`.
  4. Upgrade a Lumber Camp from L1 → L2 mid-cycle:
     - The camp does NOT vanish (regression for HF12-A).
     - The lumberjack's `gather_speed_mult` becomes `1.05`.
     - The next chop completes faster (assert effective ms equals
       `CHOP_DURATION_MS / 1.05` snapshot).
  5. Fill the Lumber Camp's storage to capacity and confirm no further
     cycles start until storage decreases (manually call
     `camp.take_from_storage(1)` after assertion).
  6. Toggle the Stone Mine off mid-cycle: current cycle finishes, no new
     cycle starts.
  After all tasks `[x]`, output `<promise>ALL_TASKS_COMPLETE</promise>`
  and create `.cursor/ralph/done`.

- [ ] **T125**: Cleanup pass:
  - Remove dead `LumberCamp.income()` call sites and any
    `apply_production_tick` branches that special-cased active-cycle
    buildings (everything is gated by `working_buildings()` × storage).
  - Ensure `ruff` / linter is clean.
  - Update `README.md` controls / gameplay summary to mention
    stonecutters, internal storage, and per-level worker bonuses (one-line
    each).
  - `pytest -q` final green run.

---

## Decisions Log

| Date       | Task   | Decision                                                                                  | Rationale                                                                                                  |
|------------|--------|-------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| 2026-04-27 | HF12-A | Hit-resolve LumberCamp panel against `extra_bottom_px=72` only (drop legacy fallback).    | Legacy fallback returned `"demolish"` for clicks on the visible Upgrade button (28 px overlap).            |
| 2026-04-27 | T96+   | Movement & gather speed bonuses are additive (per PRD F-CHAR-02), not multiplicative.     | Easier to reason about cumulative debuffs; user explicitly requested additive stacking.                    |
| 2026-04-27 | T103   | Storage capacity formula `3 + 2 × (L − 1)` = 3, 5, 7 … 21 over levels 1..10.              | User specified +2 per level on top of base 3.                                                              |
| 2026-04-27 | T111   | 3 stone clusters (constant), centre Chebyshev ≥ 12 from Town Hall, radius `r ∈ [3, 6]`.   | Verbatim user spec.                                                                                        |
| 2026-04-27 | F-WORK-13 | MINER and FARMER stay passive in Phase 12; only storage cap applies.                  | User chose "active_with_field" later → defer active gather to a follow-up phase.                           |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
|      |      |       |        |

## Notes

- All tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- All bonuses are clamped to a positive minimum (`>= 0.10`) so workers never
  freeze when temporary debuffs land in the future.
- Stone assets are placeholders for now; the disk-first asset loader allows
  swapping the PNG without code changes.
- Phase 11 sections above are kept for ralph-loop input context only — do NOT
  re-run those tasks.
