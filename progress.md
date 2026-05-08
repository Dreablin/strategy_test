# Progress - Isometric Strategy Game

## Current Status

- **Phase:** 22 - Canteen, cook, meals, and worker satiety
- **Next Task:** T251 - canteen asset loading/render wiring
- **Last Completed:** T250 - canteen asset placeholders and smoke test
- **Total Progress:** 250 / 276 (Phase 22: 5 / 31 done)

> **Archive:** Full older phase history is in **`progress_archive.md`**. Do **not** re-run completed tasks.

---

## Task Log

## Phase 22 - Canteen, cook, meals, and worker satiety

**Goal.** Add a social building **CANTEEN**, a new hireable worker **COOK**, local-only **simple meals**, shared worker satiety, and a dining flow where hungry workers reserve a canteen slot, walk there, eat in parallel, then return to work.

**Implementation notes.**

- Canteen is a social building with 10 levels.
- Level 1 local storage: `5 chicken`, `5 bread`, `5 water`, `5 simple_meal`.
- Each canteen level above 1 adds `+1` capacity to every local storage bucket and `+1` diner slot.
- Level 1 diner slots: `3`.
- `simple_meal` is local to canteens only. It must not appear in Town Hall warehouse resources and carriers must not export it.
- Cook cycle: needs assigned cook, active canteen, `1 chicken + 1 bread + 1 water`, `30_000 ms` production, `5_000 ms` rest, outputs `1 simple_meal` into canteen local storage.
- Worker satiety: max `10_000`, initial `10_000`, drains by `15` per in-game second, clamps to `[0, 10_000]`.
- Hunger trigger threshold: below `2_000`.
- Dining duration after a meal is assigned: `20_000 ms`.
- Meal waiting rule: lack of `simple_meal` does not block reserving a slot or walking to the canteen. A hungry worker who reaches a canteen with no available meal stays in the reserved diner slot and waits. Eating starts only when the canteen has a `simple_meal` available for that specific waiting worker. If several workers wait and fewer meals are available, assign meals deterministically to waiting workers one at a time; workers without an assigned meal keep waiting for the next produced meal. Consume `1 simple_meal` when a worker starts eating, then restore satiety to `10_000` and release the slot after the `20_000 ms` eating timer completes.

### 22.1 Canteen domain, config, assets, and menu

- [x] **T246**: Add RED tests for `CANTEEN` building domain: social/build menu entry, 10 max levels, configured construction cost/time, local storage buckets for `chicken`, `bread`, `water`, and `simple_meal`, level 1 capacities of `5`, per-level `+1` capacity, level 1 diner slots of `3`, and per-level `+1` diner slot.
- [x] **T247**: Implement `Canteen` building class, config/json wiring, registry/placement/bottom-bar social menu entry, local storage helpers, and capacity formulas. Run full `pytest -q`.
- [x] **T248**: Add RED tests proving `simple_meal` is not a Town Hall warehouse resource, is not displayed in Town Hall storage, and is never generated as a carrier export task.
- [x] **T249**: Implement the local-only `simple_meal` resource labels/helpers needed by canteen UI and tests without adding it to Town Hall warehouse. Run full `pytest -q`.
- [x] **T250**: Add canteen asset placeholders and `asset_meta.json` in the correct building asset folder, following existing building scale/anchor conventions. Add a render/asset smoke test for built and construction sprites.
- [ ] **T251**: Implement canteen asset loading/render wiring and make the asset smoke test green. Run full `pytest -q`.

### 22.2 Cook hiring and canteen production

- [ ] **T252**: Add RED tests for new hireable `COOK`: appears in school panel, can be queued/cancelled like other workers, starts with full satiety, has worker dot/UI fallback asset, and maps to `CANTEEN` assignment.
- [ ] **T253**: Implement cook hire wiring, worker labels/assets, school panel entry, worker-to-building mapping, and assignment. Run full `pytest -q`.
- [ ] **T254**: Add RED tests for canteen production gating: no cook means no production, inactive canteen prevents new cycles, missing any input blocks cycle start, full `simple_meal` storage blocks cycle start, existing cycle continues when active is toggled off only if current local rules for other processors require it.
- [ ] **T255**: Implement canteen processor runtime using the shared processor pattern where possible: `30_000 ms` work, consume all three inputs at cycle start or completion consistently with existing processors, output `simple_meal`, then `5_000 ms` cook rest. Run full `pytest -q`.
- [ ] **T256**: Add RED tests for carrier input tasks into canteen: chicken, bread, and water are delivered while capacity plus inbound reservations allow it; water uses the existing direct-well flow; duplicate queued/in-flight tasks do not overfill local storage.
- [ ] **T257**: Implement canteen input transport task generation and dedupe/inbound counting using existing transport queue conventions. Do not add any output transport for `simple_meal`. Run full `pytest -q`.
- [ ] **T258**: Add and implement canteen panel production status/progress tests: worker line, input/output storage lines, active toggle, production progress bar, rest/status text, upgrade/demolish controls. Run full `pytest -q`.

### 22.3 Satiety model and worker panel

- [ ] **T259**: Add RED tests for worker satiety model: every newly created/hired worker starts at `10_000`, max clamp is `10_000`, min clamp is `0`, and deterministic draining subtracts `15` per elapsed in-game second without frame-rate drift.
- [ ] **T260**: Implement satiety fields/timestamps on `Worker` and central satiety ticking in `WorkerManager.update` so every worker drains once per elapsed second. Run full `pytest -q`.
- [ ] **T261**: Add RED tests for worker panel satiety display, including idle worker, carrier carrying a resource, and worker with an active transport task.
- [ ] **T262**: Update worker panel UI to show satiety as current/max and keep existing task/resource lines intact. Run full `pytest -q`.

### 22.4 Canteen dining slots and reservation model

- [ ] **T263**: Add RED tests for canteen diner slot model: slot capacity by level, immediate reservation by worker identity, no duplicate reservation by the same worker, no over-reservation, release on dining completion, release on worker/building removal, and release on canteen demolition.
- [ ] **T264**: Implement canteen diner slot/reservation data model and cleanup helpers. Keep it independent from production storage. Run full `pytest -q`.
- [ ] **T265**: Add RED tests for canteen selection: hungry worker below `2_000` picks the nearest reachable canteen with a free slot, reserves immediately, does not require a prepared meal to reserve, and continues working if no slot/path exists.
- [ ] **T266**: Implement canteen selection and reservation helper functions in small modules/mixins, reusing 4-dir pathfinding and existing blocked-tile rules. Run full `pytest -q`.
- [ ] **T267**: Add RED tests for dining runtime: reserved worker walks to canteen, appears in a specific tile slot, waits there if no `simple_meal` is available, starts a `20_000 ms` eating timer only after a meal is assigned, consumes `1 simple_meal` when eating starts, restores satiety to `10_000` when the timer completes, releases the slot, and returns to work.
- [ ] **T268**: Implement shared dining runtime states, waiting/eating transitions, deterministic one-meal-per-worker assignment, and progress helpers without entangling them with carrier transport tasks or processor production tasks. Run full `pytest -q`.

### 22.5 Hunger check integration for all worker families

- [ ] **T269**: Add RED tests for processor/gatherer/miner/farmer hunger checks: after a completed production/gather/field cycle and before normal rest, a hungry worker attempts to reserve canteen; if blocked by missing slot/path, existing work/rest behavior continues.
- [ ] **T270**: Implement hunger hooks for processor workers, gatherers, miner, farmer, and forester at the cycle boundaries covered by T269. Run full `pytest -q`.
- [ ] **T271**: Add RED tests for blocked-cycle hunger checks: when a worker cannot start a new cycle because inputs/output/storage/target conditions block it, the hunger check still runs at a throttled retry point and does not spam reservations.
- [ ] **T272**: Implement throttled hunger checks for blocked processor/gatherer/farmer/miner states. Run full `pytest -q`.
- [ ] **T273**: Add RED tests for builders and carriers: builder checks hunger after construction completion and while idle with no construction; carrier checks after delivery completion and while idle with no transport; neither abandons an active construction or active carried item.
- [ ] **T274**: Implement builder/carrier hunger hooks and return-to-work behavior after dining. Carriers must only go to canteen when not carrying anything. Run full `pytest -q`.

### 22.6 Canteen UI, diner tiles, smoke, and final verification

- [ ] **T275**: Add and implement canteen panel diner tiles: one tile per slot, occupied/reserved state, waiting-vs-eating state, worker avatar/label, and per-diner eating progress bar only while eating. Include click-panel tests and headless render assertions.
- [ ] **T276**: Add end-to-end smoke test: build canteen, hire cook, deliver chicken/bread/water, produce `simple_meal`, drain worker satiety below threshold, reserve a dining slot, wait if no meal exists, eat for `20_000 ms` after meal assignment, restore satiety, release slot, and return to work. Final gate: full `pytest -q` plus `ruff check src tests`; update Current Status and Notes; mark Phase 22 complete only when all tasks are `[x]`.

---

## Rules For Next Phase

- Keep exactly one active task marked `[~]` at a time.
- Start new work from the first unchecked `[ ]` task in the active phase.
- Mark `[x]` only after verification (`pytest -q`, and `ruff check src tests` when relevant).
- If blocked after repeated attempts, mark `[!]` and add a row in **Issues & Blockers**.

## Decisions Log

| Date | Task | Decision | Rationale |
|------|------|----------|-----------|
| 2026-05-04 | Phase 22 | `simple_meal` is canteen-local and is not a Town Hall warehouse resource. | Meals are consumed inside canteens and should not enter global carrier export/storage loops. |
| 2026-05-04 | Phase 22 | Dining slot reservation is allowed without a prepared meal; the worker waits in the canteen until a `simple_meal` is assigned, then eats for `20_000 ms`. | Matches the requirement that hungry workers can sit in the canteen while food production catches up, and that one available meal feeds only one waiting worker. |

## Issues & Blockers

| Date | Task | Issue | Status |
|------|------|-------|--------|
| | | | |

## Notes

- Canteen building art: `assets/buildings/canteen/` (`default.png`, `construction.png`, `asset_meta.json`); swap PNGs without changing paths.
- `game.resource_catalog` holds Town Hall warehouse key allow-list, `simple_meal` display label, and guards so carriers cannot enqueue `simple_meal` deliveries to Town Hall.
- Tests run headless via `SDL_VIDEODRIVER=dummy` in `tests/conftest.py`.
- Extended history, completed phase checklists, and older decisions log: **`progress_archive.md`**.
- Pathfinding contract: **4-dir** `find_path_bfs` (no diagonals), aligned with PRD.
- Worker extension rules: **`worker_extension_guide.md`**.
- Building extension rules: **`building_extension_guide.md`**.
- Ralph-loop contract: leave exactly one `[~]` task, otherwise the next agent starts the first `[ ]` task.
