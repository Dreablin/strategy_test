# Progress — Isometric Strategy Game

## Current Status

- **Phase:** 14. Forestry expansion: forester hut, planting cycle, tree variants
- **Next Task:** T157 — add failing render tests for tree species visuals.
- **Last Completed:** T156 — implement forester worker planting cycle in workers.
- **Total Progress:** 156 / 160

> Phases 1–12 are summarised in `progress_archive.md`. Only the active phase
> plus a short context block live here. Do **not** re-run archived tasks.

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
- **Regression tests:**
  `tests/test_lumber_camp_panel.py::test_lumber_camp_click_upgrade_returns_upgrade_not_demolish`,
  `…::test_lumber_camp_click_demolish_still_returns_demolish`.

### HF13 — Procedural trees/stones: tests pin `World(world_seed=0)` (FIXED)

- **Context:** `World()` now seeds stone/tree layout from OS entropy unless
  `world_seed` is set (see `world._world_generation_rng_pair`).
- **Tests:** any case that assumes free grass at fixed tiles or stable paths
  now uses `World(world_seed=0)` (registry fixture, `test_pathfinding.py`,
  `test_workers.py`).

### HF14 — Ring-20 stone cluster invisible; `test_input` flake (FIXED)

- **Cause:** stone fill skipped any tile with Chebyshev distance from **map
  centre** ≤ `center_clear_radius` (~27 on 110×110). The mandatory centre on
  the **TH distance-20 ring** almost always lies in that zone, so its whole
  disk was skipped → only five visible clusters, none near “20 from TH”.
- **Fix:** for the ring-only centre, skip the map-centre clearing rule but
  still forbid `town_hall_footprint_tiles()`. `test_place_calls…` now uses
  `World(world_seed=0)` (extra stones near TH made unseeded paths flaky).

### HF15 — Tree groves: 8 centers, r ∈ [5, 8], 70% fill (DONE)

- Constants in `world.py`: `_TREE_GROVE_COUNT = 8`, radius +2 vs prior
  (`[5, 8]` Chebyshev), `_TREE_GROVE_FILL_PROBABILITY = 0.7`.

### HF16 — Two priority tree groves on TH rings 12 & 20 (DONE)

- Before the eight “far” grove centers: pair (ring 12, ring 20) with empty
  max-radius stone disks, Chebyshev centre separation ≥ 17; fill with relaxed
  map-centre clearing + TH footprint skip. Several tests re-pinned to
  `world_seed=2` for stable paths near the hub.

---

## Recent context (do not re-run, kept only as input for ralph-loop)

- **Phase 12** delivered worker `Characteristics`, +5 % movement / gather per
  building level (additive, source-keyed), per-building internal storage
  (`capacity(L) = 3 + 2·(L−1)`), stone deposits (`Stone(units=15)`, 6 clusters
  including one center on the TH Chebyshev ring at 20, others ≥ 12 from TH,
  `r ∈ [1, 4]`), and an active stonecutter
  gather cycle that mirrors the lumberjack one. Passive income is fully gone
  for `LUMBER_CAMP` and `STONE_MINE`; `FARM` and `IRON_MINE` keep passive
  income but obey the storage cap.
- **Phase 11** introduced the lumberjack chop cycle (walk → reserve tree →
  chop 10 s → carry wood home → deposit, with rest period and
  Active/Inactive toggle).

---

## Task Log

### Phase 13 — Performance Optimisation & Orthogonal Pathfinding

> **Goal of the phase.** The map size will grow (potentially up to 10× the
> current area). Today several core systems do per-frame O(W·H) scans of the
> grid, and BFS supports diagonal moves with corner-cut handling. We rewrite
> those hot paths so the same world boots and runs at 60 FPS on a much larger
> grid, and we restrict workers to **only horizontal/vertical movement** (no
> diagonals), as requested by the user.
>
> **Quality contract.**
>
> 1. Functional equivalence on existing maps. The only intentional behavioural
>    change is "no diagonal movement" — paths get longer, never break. Render
>    output for the visible region must match the legacy full-grid pass
>    pixel-for-pixel.
> 2. No flaky timing-based perf assertions. We measure performance via
>    **call counters** (e.g. monkeypatched `find_path_bfs`, `world_to_screen`,
>    `World.is_occupied`), not wall-clock time.
> 3. Every refactored hot path keeps a snapshot/equivalence test that proves
>    its output equals the previous implementation on a hand-built world.
> 4. No new public API additions outside what the tasks below explicitly list.
>
> **Hot paths being optimised (with current line refs):**
>
> | Site                                            | Today                                              | After Phase 13                                                            |
> |-------------------------------------------------|----------------------------------------------------|---------------------------------------------------------------------------|
> | `WorkerManager.reassign_all` (workers.py ~353)  | builds `blocked` via `for y/x in range(W,H)`       | `world.blocked_tiles()` returns a cached union (O(buildings+trees+stones))|
> | `WorkerManager._start_gather_cycle` (~561)      | same full-grid scan                                | same cached set                                                           |
> | `WorkerManager._start_return_to_camp` (~662)    | same full-grid scan                                | same cached set                                                           |
> | `pathfinding.find_path_bfs`                     | 8-direction with corner-cut guard                  | 4-direction (N/E/S/W) only, no diagonal logic at all                      |
> | `world.find_nearest_free_tree / _stone`         | 8-direction BFS expansion                          | 4-direction BFS expansion                                                 |
> | `Renderer.draw_world` (render.py ~58)           | iterates every tile every frame                    | iterates only the camera-visible tile range                               |
> | `Renderer.draw_buildings/trees/stones`          | sorts everything every frame                       | filters entities by visible tile range first                              |
> | `Renderer.world_pixel_bounds / map_origin`      | iterates every tile to find extremes               | closed-form from the four grid corners (≤ 4 `world_to_screen` calls)      |
>
> ---
>
> **How ralph-loop runs Phase 13 (read this before T126).**
>
> 1. Always work in `D:\projects\game`. Activate `.venv` (`Scripts\activate`)
>    and run tests with `pytest -q`. Tests run headless via
>    `SDL_VIDEODRIVER=dummy` from `tests/conftest.py`.
> 2. **TDD is mandatory** for every task that has a "failing tests first" line.
>    The failing test must be committed in the same task as the implementation
>    that turns it green; do not commit a red test alone.
> 3. After every task: full `pytest -q` must be green; then commit with
>    `T### – <one-line summary>`. Linter must be clean (`ruff check .`).
> 4. **Never relax a perf threshold.** Numbers in the gates below were chosen
>    so they hold deterministically on any machine. If a gate fails, fix the
>    code, not the gate.
> 5. **Never reintroduce diagonals.** Once T132 lands, any path step with
>    `abs(dx) + abs(dy) != 1` is a bug.
> 6. **Cached sets stay consistent.** Any code that mutates occupancy, trees
>    or stones MUST go through `World.mark_occupied/free`, `remove_tree`,
>    `harvest_stone`. Direct dict/list pokes are forbidden.
> 7. If a task does not fit in one ralph cycle, continue in the next cycle —
>    do **not** stop until the task's tests pass and the commit lands.
> 8. When all `[x]` are checked and `pytest -q` is green:
>    - print `<promise>ALL_TASKS_COMPLETE</promise>`.
>    - create empty file `.cursor/ralph/done`.
>
> **Useful constants / new APIs introduced by this phase:**
>
> ```python
> # src/game/world.py — new public methods (return shallow copies; cheap)
> World.occupied_tiles() -> set[tuple[int, int]]
> World.tree_tiles()     -> set[tuple[int, int]]
> World.stone_tiles()    -> set[tuple[int, int]]
> World.blocked_tiles()  -> set[tuple[int, int]]   # union of the three
>
> # src/game/pathfinding.py
> _NEIGHBORS_4 = ((0, -1), (1, 0), (0, 1), (-1, 0))   # N E S W, deterministic
>
> # src/game/render.py
> Renderer.visible_tile_range(surface, world, camera) -> tuple[int, int, int, int]
> # returns (gx_min, gy_min, gx_max_inclusive, gy_max_inclusive) clipped to grid,
> # widened by VISIBLE_TILE_MARGIN = 2 to avoid edge popping during pan.
> ```

#### 13.1 Cached blocked-tile sets in `World`

- [x] **T126**: Add failing tests in new `tests/test_world_cached_sets.py`:
  - `World()` exposes `occupied_tiles()`, `tree_tiles()`, `stone_tiles()` and
    `blocked_tiles()`, each returning a `set[tuple[int, int]]`.
  - `occupied_tiles()` is empty on a fresh `World()` (Town Hall is placed by
    the registry, not the world).
  - After `world.mark_occupied(5, 5, 2, 2)`, `occupied_tiles()` equals
    `{(5,5),(6,5),(5,6),(6,6)}`.
  - After `world.free(5, 5, 2, 2)`, `occupied_tiles()` is empty.
  - `tree_tiles()` equals the set of tiles `(gx, gy)` where
    `world.tree_at(gx, gy) is not None`. Calling `world.remove_tree(gx, gy)`
    drops that tile from the set.
  - `stone_tiles()` mirrors trees and shrinks only when
    `world.harvest_stone(gx, gy)` brings the stone to `is_depleted`.
  - `blocked_tiles()` equals `occupied_tiles() | tree_tiles() | stone_tiles()`
    after every mutation listed above.
  - **Mutation isolation test:** `s = world.occupied_tiles(); s.add((9,9))`
    must NOT corrupt the world's internal state — `world.occupied_tiles()`
    called again must still return the original set without `(9, 9)`.
  Tests must FAIL first (the methods do not exist yet).

- [x] **T127**: Implement the cached sets in `src/game/world.py`:
  - Extend `__slots__` with `_occupied_tiles`, `_tree_tiles`, `_stone_tiles`.
  - Initialise as empty `set` in `__init__`.
  - Maintain them inside `mark_occupied`, `free`, `_init_trees`,
    `remove_tree`, `_init_stones`, `harvest_stone`. (Keep `_occupied: list[list[bool]]`
    for now — it is still used by `is_occupied`.)
  - Public getters return `set(self._occupied_tiles)` (copy) etc., to keep
    callers from mutating internal state. `blocked_tiles()` returns the
    union as a fresh `set`.
  - Run `pytest -q tests/test_world_cached_sets.py` — green.

- [x] **T128**: Add failing tests in new `tests/test_world_blocked_no_grid_scan.py`:
  - Build a `World`, place a Town Hall + 1 Lumber Camp, and assert that
    `world.blocked_tiles()` returns the correct union.
  - **No-scan guarantee:** `monkeypatch.setattr(World, "is_occupied",
    lambda *_: pytest.fail("blocked_tiles must not call is_occupied"))`,
    then call `world.blocked_tiles()`; the test passes only if `is_occupied`
    is never called.
  Tests must FAIL first if the implementation falls back to `is_occupied`.

- [x] **T129**: Refactor `WorkerManager.reassign_all`,
  `WorkerManager._start_gather_cycle`, `WorkerManager._start_return_to_camp`
  in `src/game/workers.py`:
  - Replace each `blocked = {(x, y) for y in range(world.height) for x in range(world.width) if world.is_occupied(x, y)}`
    block (3 occurrences) with `blocked = world.blocked_tiles()`.
  - The subsequent `blocked.update(world.iter_alive_trees())` /
    `iter_stones()` lines are now redundant — drop them.
  - `blocked.discard(worker.current_tile)` stays as-is.
  - Run **the entire** test suite — green. No worker behaviour test should
    change.

- [x] **T130**: Add failing equivalence test in
  `tests/test_workers_blocked_equivalence.py`:
  - Build a `World`, place 3 buildings, harvest one stone, leave others.
  - Compute `legacy = {(x, y) for y in range(world.height) for x in
    range(world.width) if world.is_occupied(x, y)} | set(t for t, _ in
    world.iter_alive_trees()) | set(t for t, _ in world.iter_stones())`.
  - Assert `world.blocked_tiles() == legacy`.
  - Repeat after each of: placing another building, demolishing one,
    harvesting a stone fully (depleting it), and removing a tree.
  Implement nothing new — this test pins the equivalence of T127's
  cached sets to the legacy scan.

#### 13.2 Pathfinding: 4-direction only

- [x] **T131**: Add failing tests in `tests/test_pathfinding_4dir.py`:
  - On an empty 6×6 world, `find_path_bfs(world, (0, 0), (3, 3), set())`
    returns a path whose length equals `Manhattan((0,0),(3,3)) + 1` = 7.
  - Every consecutive pair `(p[i], p[i+1])` satisfies
    `abs(dx) + abs(dy) == 1` (no diagonals anywhere).
  - "Diagonal-wall" pattern: place buildings at (1, 0) and (0, 1) on a 4×4
    world; `find_path_bfs((0, 0), (1, 1), blocked)` returns `None`
    (legacy 8-dir would have corner-cut here). Goal becomes reachable only
    when one of the blockers is removed.
  - Determinism: two consecutive calls with identical args return identical
    lists (`==` on the result, including order).
  - Reachability: any pair of grass tiles with no blocker between them
    yields a path; same `start == goal` returns `[start]`.
  Tests must FAIL first.

- [x] **T132**: Switch `src/game/pathfinding.py` to 4-direction:
  - Replace `_NEIGHBORS_8` with `_NEIGHBORS_4 = ((0, -1), (1, 0), (0, 1),
    (-1, 0))` (deterministic order: N, E, S, W).
  - Drop the entire `if dx != 0 and dy != 0: …` corner-cut guard.
  - Update the module docstring: "Deterministic 4-direction BFS over world
    grass tiles (no diagonal movement)."
  - Run all tests; expect any test that asserted 8-dir paths to fail —
    those must be updated in T135.

- [x] **T133**: Add failing tests in
  `tests/test_world_resource_search_4dir.py`:
  - `find_nearest_free_tree` expansion uses 4-dir only: place a tree at
    (5, 5) reachable only via diagonals (i.e. (4, 4) is the worker, walls at
    (5, 4) and (4, 5)) and assert the function returns `None` rather than
    "magically" reaching the tree through a diagonal step.
  - With orthogonal access (no walls), the function still returns the tree
    tile and the BFS frontier never visits a non-orthogonal neighbour.
  - Same coverage for `find_nearest_free_stone`.
  Tests must FAIL first.

- [x] **T134**: Switch `src/game/world.py`:
  - Replace `_NEIGHBORS_8` (line 15) with `_NEIGHBORS_4` and use it in both
    `find_nearest_free_tree` and `find_nearest_free_stone`.
  - Module-level `_NEIGHBORS_8` symbol is removed (also from
    `pathfinding.py` if duplicated).
  - Run tests — green.

- [x] **T135**: Update existing tests that assumed diagonal pathing.
  - Audit the suite: `grep -R "neighbors_8\|diagonal\|NEIGHBORS_8\|len(path) == 4\|corner-cut" tests/`.
  - For each test that asserts a specific path length / shape, update the
    expected value to the 4-dir Manhattan distance + 1, or rewrite the
    scenario so the path is uniquely determined.
  - Document each update in the commit message (one bullet per file).
  - Run `pytest -q` — green.

#### 13.3 Render viewport culling

- [x] **T136**: Add failing tests in `tests/test_render_culling.py`:
  - `Renderer.visible_tile_range(surface, world, camera)` returns
    `(gx_min, gy_min, gx_max, gy_max)` (max values inclusive), all clipped
    to `[0, world.width-1] × [0, world.height-1]`, widened by
    `VISIBLE_TILE_MARGIN = 2` on each side.
  - Camera offset that scrolls everything off-screen returns an empty
    range (`gx_max < gx_min`).
  - For an 800×600 surface centred on a 100×100 grid, the visible tile
    count is bounded above by `((800/TILE_W) + 2*MARGIN + 4) *
    ((600/TILE_H) + 2*MARGIN + 4)`. Assert the actual count is `<= 1500`
    (a safe upper bound, ~ 1/6 of the full grid).
  - **Counter-based sanity:** monkeypatch `world_to_screen` to count calls;
    drawing one frame on a 100×100 world calls it `<= 4 * (W*H total)` is
    forbidden — assert call count `< 2_000`. (Today it would be ~ 4·10_000.)
  Tests must FAIL first.

- [x] **T137**: Implement viewport culling in `src/game/render.py`:
  - Add module constant `VISIBLE_TILE_MARGIN = 2`.
  - Implement `Renderer.visible_tile_range(surface, world, camera)` using
    the inverse iso transform on the four screen corners and clamping to
    grid bounds. Add a 2-tile margin on each side.
  - Rewrite `draw_world` to iterate only `(gx, gy)` inside the visible
    range.
  - In `draw_buildings`, after sorting, drop entities whose footprint
    bounding box (in tile space) does not intersect the visible range.
  - In `draw_trees` and `draw_stones`, filter `iter_alive_trees()` /
    `iter_stones()` by the same range before sorting.
  - In `draw_workers`, skip workers whose interpolated tile is outside the
    range (unless the worker is mid-path entering the range — easiest:
    use a small margin and just check `current_tile`).
  - Run all rendering tests — green.

- [x] **T138**: Add failing pixel-equivalence test in
  `tests/test_render_visual_equivalence.py`:
  - Build a deterministic `World` (fixed seed by way of `GRID_SIZE`).
  - Render a 320×240 surface twice:
    1. Force-iterate every tile (`Renderer.draw_world_full(...)` — a
       test-only helper that bypasses culling, OR call the legacy code by
       monkeypatching `visible_tile_range` to return the full grid).
    2. Use the new culling path.
  - Compute `pygame.image.tobytes(surface, "RGBA")` for the visible region
    bbox (everything except a 1-px safety border) and assert byte equality.
  - This proves "no quality lost" beyond what the user already accepted
    (4-direction movement).
  Tests must FAIL first if culling drops or shifts a pixel.

- [x] **T139**: Add failing test in `tests/test_render_pixel_bounds_o1.py`:
  - Monkeypatch `game.iso.world_to_screen` to wrap a counter.
  - Call `Renderer.world_pixel_bounds(world)` — counter must be `<= 4`.
  - Call `Renderer.map_origin(surface, world)` — counter must be `<= 4`.
  - Returned bounds equal the legacy (full-grid) computation on a small world.
  Tests must FAIL first (today both methods iterate the entire grid).

- [x] **T140**: Replace `_compute_grass_origin` and
  `Renderer.world_pixel_bounds` with closed-form versions:
  - The min/max screen coordinates of the grid are achieved at the four
    grid corners only: `(0, 0)`, `(W-1, 0)`, `(0, H-1)`, `(W-1, H-1)`.
  - Compute the four `world_to_screen(...)` values once each, derive
    `min_x / min_y / max_x / max_y` from them.
  - `map_origin` reuses those bounds, no extra calls.
  - Run all tests — green.

#### 13.4 Localised worker assignment

- [x] **T141**: Add failing tests in `tests/test_workers_local_assignment.py`:
  - Place 1 idle worker and N=10 unstaffed buildings of the matching type
    spread across the world, with one of them obviously closer (Manhattan
    distance 3) than the rest (≥ 20).
  - Wrap `find_path_bfs` with a counter monkeypatch.
  - After `worker_manager.reassign_all()`:
    1. The worker's `assigned_building` is the closest one.
    2. The counter is `<= K * len(approach_tiles)` where `K = 2` (i.e., we
       tried at most 2 candidate buildings before locking the closest in).
  Tests must FAIL first.

- [x] **T142**: Modify `WorkerManager.reassign_all`:
  - Sort `targets` by `manhattan(worker.current_tile,
    building_center_tile(target))` ascending before iterating.
  - Inside the loop, once a path is found, break — already done; just
    ensure the sort is in place before the `for target in targets:` loop.
  - No other behavioural change.
  - Run all worker tests — green.

#### 13.5 End-to-end perf gate

- [x] **T143**: Add failing perf-gate test
  `tests/test_perf_smoke_phase13.py`:
  - Use `monkeypatch.setattr(game.config, "GRID_SIZE", 100)` and reload
    `game.world` / `game.pathfinding` in the test (or use a fixture that
    rebuilds those modules with the override). If reloading is brittle,
    pass an injected `grid_size` to a temp helper world; the goal is just
    a 100×100 grid for the test.
  - Place a Town Hall, 5 Lumber Camps, 5 Stone Mines, hire 5 lumberjacks,
    5 stonecutters; advance 100 simulated frames at 16 ms per frame.
  - Wrap with monkeypatch counters:
    - `pathfinding.find_path_bfs` calls `<= 250` total.
    - `World.is_occupied` calls `<= 6_000` total (was O(W·H · frames)).
    - `iso.world_to_screen` calls (during one rendered frame at the end)
      `<= 4_000`.
  - Tests must FAIL first if any of T126–T142 regresses.

- [x] **T144**: If T143 reds, do not relax thresholds. Re-audit which call
  site exceeds the budget (counter dump in test failure output) and fix
  the implementation. Re-run; commit only when green.

#### 13.6 Cleanup, docs, end-of-phase smoke

- [x] **T145**: Cleanup pass:
  - `grep -RIn "for y in range(world.height)" src/` and
    `grep -RIn "for x in range(world.width)" src/` MUST return zero hits.
  - Delete dead `_NEIGHBORS_8` symbols anywhere they remain.
  - Run `ruff check --fix .` until clean.
  - `pytest -q` final green run.

- [x] **T146**: Update PRD and progress decisions log:
  - PRD: change the `game.pathfinding` API block to "4-direction BFS" and
    add a new `F-PATH-01` requirement saying "movement is restricted to
    horizontal and vertical (no diagonals)".
  - PRD: add `NFR-PERF-03` ("renderer must iterate only visible tile range
    each frame") and `NFR-PERF-04` ("worker assignment / gather scheduling
    must run in O(buildings + entities), not O(W·H), per frame").
  - PRD: add the new `Renderer.visible_tile_range` and `World.*_tiles()` /
    `blocked_tiles()` entries under §6 API Specification.
  - `progress.md` Decisions Log: add the orthogonal-pathing decision and
    the cached-set decision (see template below).

- [x] **T147**: Add a 1-paragraph note to `README.md` under "Performance":
  workers move only N/E/S/W; visible-tile rendering keeps frame cost
  independent of map size; supported map sizes scale to ~10× the default
  area.

- [x] **T148**: End-of-phase smoke `tests/test_smoke_phase13.py`
  (`SDL_VIDEODRIVER=dummy`):
  1. Boot a default `World()`. Place Town Hall + Lumber Camp + Stone Mine.
  2. Hire one lumberjack and one stonecutter. Advance 60_000 ms in 16 ms
     steps using the worker manager.
  3. Assert that **every** path step taken by every worker satisfies
     `abs(dx) + abs(dy) == 1` (record path tiles via a counter wrapper).
  4. Assert that `find_path_bfs` was called fewer times than the
     pessimistic "scan every tick" upper bound (`< 200`).
  5. Render exactly one frame to a 320×240 surface; assert no exception
     and the surface contains at least one non-background pixel.
  6. After all `[x]` are checked: print `<promise>ALL_TASKS_COMPLETE</promise>`
     and create empty file `.cursor/ralph/done`.

### Phase 14 — Forestry Expansion (Forester + Forester Hut + Tree Species)

> **Goal of the phase.** Add an active reforestation loop: a new building
> (`FORESTER_HUT`) and worker role (`FORESTER`) that periodically plant trees
> around the hut. Newly planted trees start at the smallest stage, then grow
> automatically over time. Also introduce 3 visual tree variants (asset-level
> difference only) while preserving existing gameplay rules (only fully-grown
> trees can be chopped).
>
> **Functional requirements for this phase (user contract):**
>
> 1. New building: **Forester Hut**. Max level = 1 (no upgrades), supports
>    Active/Inactive toggle exactly like gather buildings.
> 2. New worker: **Forester**. When assigned and active:
>    - leaves hut,
>    - walks to a **random free** tile within radius 15 from hut,
>    - spends 5_000 ms planting on that tile,
>    - planted tree appears at the smallest stage.
> 3. Tree growth:
>    - 4 stages total (existing ladder),
>    - automatic growth tick every 30_000 ms,
>    - only fully-grown stage remains chop-eligible.
> 4. Tree variants:
>    - 3 species/types with different assets only,
>    - no gameplay/stat difference between species.
>
> **Ralph-loop execution notes (same discipline as Phase 13):**
>
> - TDD-first for each task with "failing tests first".
> - After each task: targeted tests + full `pytest -q` + `ruff check src tests`.
> - Keep deterministic tests by pinning `World(world_seed=...)` where pathing /
>   placement assumptions depend on map layout.
> - No PRD edits outside tasks that explicitly require PRD/docs sync.

#### 14.1 Tree domain: species + timed growth

- [x] **T149**: Add failing tests in new `tests/test_trees_species_growth.py`:
  - `Tree` supports exactly 3 species ids (e.g. `0..2` or enum).
  - New planted tree starts at smallest stage (`SAPLING`/equivalent).
  - Growth API advances one stage every 30_000 ms and caps at mature stage.
  - `can_chop` (or equivalent contract) is `False` until mature, `True` at mature.
  - Stage progression is deterministic and independent from species.

- [x] **T150**: Implement species + growth timing in `src/game/trees.py`:
  - Add species field to `Tree` (asset-facing only).
  - Add growth timestamp/timer support (`next_growth_at_ms` or accumulated timer).
  - Add methods/helpers to progress growth in fixed 30_000 ms steps.
  - Preserve existing behaviour for mature legacy trees generated at world init.
  - Run `pytest -q tests/test_trees_species_growth.py` -> green.

#### 14.2 World integration for planted trees and global growth ticks

- [x] **T151**: Add failing tests in `tests/test_world_tree_growth_runtime.py`:
  - `World.plant_tree(x, y, now_ms, species=...)` (or chosen API) creates
    smallest-stage tree on valid free tile.
  - Planting is rejected on occupied / stone / existing-tree / TH footprint tile.
  - `World.update_tree_growth(now_ms)` advances planted trees each 30_000 ms.
  - Matured trees become discoverable by lumberjack search/chop flow.

- [x] **T152**: Implement world-level planting/growth hooks in `src/game/world.py`:
  - Add plant-tree API used by forester cycle.
  - Add periodic growth update method called from main worker/game update path.
  - Ensure cached tile sets remain correct and no full-grid scans are introduced.
  - Keep generated trees compatible with new species field (assign deterministic species).

#### 14.3 New building: Forester Hut

- [x] **T153**: Add failing tests in `tests/test_forester_hut_building.py`:
  - `FORESTER_HUT` exists in building registry/build menu.
  - Building has level fixed at 1 (upgrade attempt fails cleanly).
  - Building supports active toggle state and UI status text parity with other camps.
  - Placement footprint and spacing rules follow normal 2x2 producer buildings.

- [x] **T154**: Implement `ForesterHut` building + registration:
  - Add `src/game/buildings/forester_hut.py`.
  - Register type tag, costs, unlock gate, panel wiring, and active toggle handling.
  - Ensure no per-cycle passive income is added for this building.
  - Add/adjust minimal asset metadata placeholders if needed.

#### 14.4 New worker role: Forester planting cycle

- [x] **T155**: Add failing tests in `tests/test_forester_cycle.py`:
  - `Worker("FORESTER")` can be hired and assigned only to `FORESTER_HUT`.
  - Chooses a random **reachable free tile** within Chebyshev radius 15 from hut.
  - Enters planting state for exactly 5_000 ms on target tile.
  - On completion, world gains one smallest-stage tree at target tile.
  - Inactive hut blocks starting new cycle but allows in-progress cycle to finish.

- [x] **T156**: Implement forester cycle in `src/game/workers.py`:
  - Add worker states for go_to_plant_tile / planting / return (or existing pattern).
  - Reuse BFS/path contracts (4-dir) and blocked-tiles logic.
  - Target selection uses RNG with deterministic injection for tests
    (`now_ms_fn`-style and/or RNG dependency).
  - Wire cycle into `reassign_all()` and regular `update()`.

#### 14.5 Rendering and assets for 3 tree species

- [ ] **T157**: Add failing render tests in `tests/test_render_tree_species.py`:
  - Renderer chooses sprite by `(species, stage)` combination.
  - Fallback path works when specific species asset is missing.
  - Existing depth/layering order for trees is preserved.

- [ ] **T158**: Implement species-aware tree asset loading/render:
  - Extend tree asset keying and metadata lookup for 3 variants.
  - Keep gameplay untouched (only visuals differ).
  - Provide procedural fallback for each species/stage pair.

#### 14.6 End-to-end + docs

- [ ] **T159**: Add end-to-end smoke test `tests/test_smoke_phase14.py`:
  1. Boot world + TH + Forester Hut.
  2. Hire one forester, run simulated time until at least one planted tree appears.
  3. Advance time to mature that tree via growth ticks.
  4. Verify a lumberjack can target/chop the matured planted tree.
  5. Assert no exceptions during one rendered frame with mixed species trees.

- [ ] **T160**: Docs/progress sync and phase completion:
  - Update PRD sections for new building/worker, growth timing, and species visuals.
  - Update `progress.md` Current Status + Decisions Log with key choices
    (random target selection policy, growth scheduler source of truth).
  - Final full-suite run (`pytest -q`, `ruff check src tests`).
  - Mark all Phase 14 tasks `[x]`, then emit
    `<promise>ALL_TASKS_COMPLETE</promise>` and create `.cursor/ralph/done`.

---

## Decisions Log

| Date       | Task    | Decision                                                                                 | Rationale                                                                                              |
|------------|---------|------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| 2026-04-27 | HF12-A  | Hit-resolve LumberCamp panel against `extra_bottom_px=72` only (drop legacy fallback).   | Legacy fallback returned `"demolish"` for clicks on the visible Upgrade button (28 px overlap).        |
| 2026-04-27 | T96+    | Movement & gather speed bonuses are additive (per PRD F-CHAR-02), not multiplicative.    | Easier to reason about cumulative debuffs; user explicitly requested additive stacking.                |
| 2026-04-27 | T103    | Storage capacity formula `3 + 2 × (L − 1)` = 3, 5, 7 … 21 over levels 1..10.             | User specified +2 per level on top of base 3.                                                          |
| 2026-04-27 | T111    | 3 stone clusters (constant), centre Chebyshev ≥ 12 from Town Hall, radius `r ∈ [1, 4]`.  | Verbatim user spec.                                                                                    |
| 2026-04-27 | F-WORK-13 | MINER and FARMER stay passive in Phase 12; only storage cap applies.                   | User chose "active_with_field" later → defer active gather to a follow-up phase.                       |
| 2026-04-27 | T132    | BFS uses 4 neighbours only (N/E/S/W), no diagonal moves and no corner-cut handling.      | User asked workers to walk only horizontally/vertically. Side benefit: simpler BFS, fewer edge cases.  |
| 2026-04-27 | T127    | `World` maintains shadow `set` indices for occupied / tree / stone tiles.                | Eliminates per-frame O(W·H) grid scans in worker dispatch; enables 10× larger maps without lag.        |
| 2026-04-27 | T137    | Rendering iterates only `Renderer.visible_tile_range(...)` plus 2-tile margin.           | Frame cost becomes a function of viewport size, not map size; pixel-equivalence test guards quality.   |

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
- After Phase 13, paths get ~ 40 % longer on average for diagonal goals — this
  is intentional. Travel time bonuses (Phase 12 +5 % per level) still apply.
- Phase 11 / Phase 12 details live in `progress_archive.md`.
