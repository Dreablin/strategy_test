# Building Extension Guide

This file is the coding-agent contract for adding buildings without scattering
logic across unrelated modules or duplicating old behavior.

## Core Rule

Buildings define structure and local state. Workers and carriers drive active
economy behavior.

Do not add passive `Building.income()` production for active resources. New
resources should flow through local building storage, worker cycles, and carrier
transport tasks.

## Current Building Touchpoints

- `src/game/buildings/<name>.py`: building class, local storage, active flag,
  progress helpers, and type-specific methods.
- `src/game/buildings/base.py`: shared `Building` contract: `type_tag`,
  `footprint`, `level`, `grid_pos`, `construction_site`, `max_level()`.
- `src/game/buildings/registry.py`: placement, demolition, upgrades,
  construction site creation, world occupancy, and special placement rules.
- `src/game/settings/buildings/<name>.json`: construction and upgrade costs.
  Keep per-building construction data and building-owned worker effects here,
  not hard-coded in `config.py` or worker runtime.
- `assets/buildings/<folder>/`: building sprites and `asset_meta.json`.
- `src/game/assets.py`: type tag to asset-folder mapping and procedural fallback
  palette when needed.
- `src/game/ui/bottom_bar.py`: build menu category and `BUILD_MENU_SELECT`
  event.
- `src/game/input.py`: placement type imports, panel routing, upgrade/demolish
  click handling, and special panel selection.
- `src/game/ui/*_panel.py`: building-specific panels when the generic
  `BuildingPanel` is not enough (for example `vineyard_farm_panel.py` for
  `VINEYARD_FARM`).
- `src/game/transport_tasks.py`: carrier tasks for construction, input refill,
  water input, and output export.
- `src/game/worker_*.py`: worker runtime when a building needs a staffed worker.

## Adding a New Building

1. Create the building class.

   - Add `src/game/buildings/<name>.py`.
   - Subclass `Building` or an existing mixin such as `StorageMixin`.
   - Set `type_tag` as uppercase snake case and `footprint` if it is not the
     default `(2, 2)`.
   - Keep only local state and small capability methods on the building.
   - For processors, prefer capability names like `input_amount()`,
     `input_capacity()`, `output_amount()`, `output_capacity()`,
     `add_<resource>_in()`, `take_<resource>_in()`, and
     `add_<resource>_out()`.
   - When a building has **multiple distinct input or output storages** (for
     example `COW_FARM` with wheat and water inputs plus beef and hide
     outputs), use explicit per-slot helpers (`wheat_amount`, `beef_amount`,
     `take_hide_out`, and so on) instead of overloading a single generic pair.
     Recipe and processor runtime still read amounts from JSON; keep balance
     numbers in `src/game/settings/buildings/<name>.json`, not in code
     constants.

2. Add construction settings.

   - Create `src/game/settings/buildings/<name>.json`.
   - Include levels that should require construction resources and build time.
   - Most normal buildings have 10 levels. Use explicit exceptions for special
     buildings such as `FIELD`, `WELL`, and `TOWN_HALL`.
   - Do not add duplicate construction cost tables in code.
   - If the building should improve its assigned worker, add
     `worker_effects.by_level.<level>.assigned_worker` in this JSON. These
     effects apply only to `worker.assigned_building is building`.

3. Register placement and menus.

   - Add imports/mapping where placement selects building classes.
   - Add the building to `BottomBar` in the correct category: resource, social,
     processing, or dev.
   - Add or adjust placement tests for category, valid tiles, footprint, tech
     gates, and special overlap rules.
   - Keep `FIELD`, `WELL`, and `TOWN_HALL` special-case behavior explicit.

4. Add assets.

   - Create `assets/buildings/<folder>/asset_meta.json`.
   - Add ready sprites named `level_01.png` through `level_10.png` when levels
     exist, plus construction sprites such as `construction_01.png`.
   - If the folder name is not the lower-case type tag, update
     `_BUILDING_FOLDER` in `assets.py` (for example, `MILL` uses `windmill`).
   - Add a procedural palette in `assets.py` when a fallback color matters.
   - Asset files should be disk-first but missing files must not crash tests.

5. Add UI panel behavior.

   - Use `BuildingPanel` if generic name/level/storage/upgrade/demolish is
     enough.
   - Create a focused `src/game/ui/<name>_panel.py` only when the building needs
     custom controls, multiple storage counters, progress bars, queue UI, or
     special disabled states.
   - Route draw and click handling from `input.py`.
   - Panels must absorb clicks across their full frame and must not duplicate
     the same local stock with two counters.

6. Add production and workers only in the right layer.

   - Raw producers expose local output storage. Worker runtime belongs in the
     relevant `worker_*.py` module.
   - Indoor processors should use `ProcessorSpec` in `worker_processing.py`
     unless their cycle is materially different.
   - Carrier delivery/export logic belongs in `transport_tasks.py` and
     `worker_transport.py`, not inside building classes.
   - Water is never stored in Town Hall. Water consumers should expose water
     input capability methods and use the existing water transport path.
   - Building `assigned_worker` effects never apply to carriers just because a
     carrier delivers to or picks up from the building.

7. Extend transport deliberately.

   - Add task builders in `transport_tasks.py` for new construction inputs,
     processor refills, water inputs, or output exports.
   - **Multi-output processors:** each warehoused Town Hall resource needs its
     own export task generator (for example beef and hide each have a
     `cow_farm_*_output_transport_tasks` builder). Each unit of local output
     typically becomes one low-priority `TransportTask` toward `TOWN_HALL`.
     Extend `worker_transport.py` for pickup (`take_*_out`), rollback on
     failed path (`add_*_out`), `_next_transport_task` source presence, and
     stale-queue removal when the source slot is empty, mirroring existing
     chicken or single-output processor patterns.
   - The task builder should express desired deliveries only. Let
     `worker_transport.py` handle queue deduplication, priority selection,
     carrier movement, invalid-task rerouting, and water-specific reroute rules
     (carried water is dropped rather than sent to Town Hall).
   - Capacity checks must account for inbound queued/carried deliveries, not
     only current local storage. Player panels still show only real stored
     amounts.
   - Normal resources carried to a demolished target should return to Town Hall.
     Water should be cleared instead because Town Hall does not store water.
   - Keep priorities explicit: construction is high priority; regular refills
     and output exports are low priority unless gameplay requires otherwise.
   - **Grape exports:** add a `vineyard_farm_grape_output_transport_tasks` (or
     similarly named) builder in `transport_tasks.py`, enqueue it from
     `WorkerManager.update` via `worker_transport.py`, and extend carrier pickup
     / stale-queue / rollback paths for `grapes` sourced from `VINEYARD_FARM`
     the same way wheat from `FARM` or boards from a mill are handled. Do not
     attach export logic to the `VineyardFarm` class itself.

8. Handle lifecycle.

   - Completed work buildings should start unstaffed.
   - Construction and upgrades should create/use `ConstructionSite` when
     requirements exist.
   - Upgrades should disable active production where appropriate until build
     completion.
   - Demolition must release world occupancy and notify workers through the
     registry/worker manager flow.

## Winery (`WINERY`)

The Winery is a standard indoor processor building:

- **Worker:** `WINEMAKER` (advanced tier, one per winery).
- **Recipe:** 3 grapes → 1 wine (60 s cycle, 10 s rest).
- **Input storage:** `grapes` — capacity starts at 3, +1 per level.
- **Output storage:** `wine` — capacity starts at 3, +1 per level.
- **Settings source:** `src/game/settings/buildings/winery.json` (single source
  of truth for all balance constants including storage capacity by level,
  production timings, and construction costs).
- **Panel:** `src/game/ui/winery_panel.py` with grape/wine storage rows,
  progress bar, and active toggle.
- **Transport:**
  - Input: `winery_input_transport_tasks` delivers grapes from Town Hall.
  - Output: `winery_output_transport_tasks` exports wine to Town Hall.
  - Carrier pickup uses `take_wine` on the Winery source.
  - Carrier deposit uses `add_grapes` on the Winery target.
- **Production runtime:** uses `WINERY_PROCESSOR` ProcessorSpec in
  `worker_processing.py`.
- **Status:** `worker_status.py` has a `WINERY` block reporting No worker,
  Inactive, No grapes, Output full, Processing, and Resting.

## Vineyard Farm (`VINEYARD_FARM`) and Vineyard plot (`VINEYARD`)

This is the **farm + separate plots** pattern: one staffed building holds local
output storage and worker AI; many small footprint **plot** buildings provide
the world-facing growth state. Keep wheat `FIELD` / `FARM` behavior isolated—do
not route grape growth or harvest through the wheat field pipeline.

### Types and responsibilities

- **`VINEYARD_FARM`**: normal footprint farm building with `active`, local grape
  counters (`grapes_amount` / `grapes_capacity` / `add_grapes_to_storage` /
  `take_grapes_from_storage`), harvest radius read from JSON, and a dedicated
  `VineyardFarmPanel` in `src/game/ui/vineyard_farm_panel.py` routed from
  `input.py`. Balance and worker-effect tables live in
  `src/game/settings/buildings/vineyard_farm.json` (single source of truth).
- **`VINEYARD`**: `1×1` plot building with growth stage fields and
  `tick_growth` / `mark_harvested` semantics driven by
  `src/game/settings/buildings/vineyard.json`. Asset loading follows the same
  disk-first + procedural fallback rules as other buildings; growth-stage
  filenames and metadata belong with the vineyard asset folder and JSON, not
  hard-coded in Python.

### Placement and UI

- Register both types in placement maps and the bottom bar like other
  constructibles. Placement may need radius or gate checks—mirror existing farm
  patterns in `placement.py` / tests.
- **Map click:** `VINEYARD` is intentionally **not** a modal panel target (same
  idea as `FIELD`): see `input.py` where `FIELD` and `VINEYARD` are excluded from
  `self._panel` assignment. Players still see plot state on the map and in the
  Vineyard Farm panel’s production copy.

### Workers and transport (pointers only)

- The existing **`FARMER`** staffs both `FARM` and `VINEYARD_FARM`; see
  `worker_hiring.worker_compatible_building_types` and `worker_farming.py` for
  the split state machines (`_update_wheat_farm_farmer` vs
  `_update_vineyard_farm_farmer`), plot reservations, and harvest completion.
- Carrier grape export is described under **§7 Extend transport** above; keep
  enqueue/dedupe in the transport layer.

## Restaurant (`RESTAURANT`)

The Restaurant is a social dining building for advanced-tier workers:

- **Worker:** `COOK` (basic tier; `COOK` can work in both `CANTEEN` and
  `RESTAURANT` — see `worker_hiring.worker_compatible_building_types`).
- **Recipe:** 1 bread + 1 wine + 1 beef → 1 elite_meal (45 s cycle, 8 s rest).
- **Input storage:** `bread`, `wine`, `beef` — capacity starts at 3, +1 per
  level.
- **Output storage:** `elite_meal` (local-only, never exported to Town Hall) —
  capacity starts at 3, +1 per level.
- **Settings source:** `src/game/settings/buildings/restaurant.json` (single
  source of truth for storage capacity, diner slot capacity, production timings,
  recipe, and construction costs).
- **Panel:** `src/game/ui/restaurant_panel.py` with storage rows, production
  progress bar, diner tiles, and active toggle.
- **Transport:**
  - Input: `restaurant_input_transport_tasks` delivers bread, wine, and beef
    from Town Hall.
  - Output: **none** — `elite_meal` is local-only like `simple_meal` and must
    never be exported.
- **Production runtime:** uses `RESTAURANT_PROCESSOR` ProcessorSpec in
  `worker_processing.py`.
- **Status:** `worker_status.py` has a `RESTAURANT` block reporting No worker,
  Inactive, Missing inputs, Output full, Processing, and Resting.

### Generic Dining-Building Rules

Dining selection and dining runtime are generalized so both Canteen and
Restaurant share the same reservation, walking, eating, slot release, and
return-to-work code:

- **Worker tier determines dining building.** Basic workers eat at `CANTEEN`;
  advanced workers eat at `RESTAURANT`. Worker tier is resolved by
  `worker_tiers.worker_tier(type_tag)`.
- **Dining buildings implement a duck-typed interface:** `meal_resource_key()`,
  `dining_tier()`, `_diner_occupants`, `_reserved_meal_workers`,
  `diner_slot_capacity()`, and local-storage helpers.
- **`canteen_dining.py`** provides slot/meal reservation helpers that accept any
  building implementing the dining interface (parameter typed as `Any`).
- **`canteen_selection.py`** scans `_DINING_BUILDING_TYPES` (currently
  `{"CANTEEN", "RESTAURANT"}`) and filters by `dining_tier()` versus worker
  tier.
- **`worker_dining.py`** runs walking, eating, slot release, and return-to-work
  for any building implementing the dining interface.

### Local-Only Meal Resources

- `simple_meal` (Canteen) and `elite_meal` (Restaurant) are both local-only.
- `resource_catalog.is_local_only_meal(key)` returns `True` for both.
- Transport task builders check `is_local_only_meal` and refuse to create export
  or inbound tasks for these resources.
- Town Hall warehouse does not store these resources.

## Tests to Add or Update

Use focused tests first, then run the full suite.

- Building class tests: footprint, level cap, storage capacity, active state,
  progress helpers.
- Config/construction tests: settings JSON is loaded and upgrade requirements
  behave as expected.
- Placement tests: menu selection, valid/invalid tiles, occupancy, spacing,
  tech gates, and special resource overlap.
- Asset/render tests: sprite loading, fallback behavior, metadata scale/anchor,
  construction sprite rendering.
- Panel tests: visible storage, progress, upgrade/demolish states, click
  absorption.
- Transport tests: input refill, water delivery, output export, inbound-count
  capacity, busy temporary sources, and demolished source/target reroutes.
- Worker/runtime tests when the building needs a worker.

Before marking a task done, run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest
```

## Avoid

- Putting construction costs back into `config.py` when a building JSON should
  own them.
- Adding production directly to `Building.income()`.
- Hiding transport queue decisions inside a building class.
- Normalizing `FIELD`, `VINEYARD`, `WELL`, or `TOWN_HALL` into ordinary building
  behavior (including forcing a map panel on terrain plots that intentionally
  skip `BuildingPanel`).
- Adding a custom panel when the generic panel is enough.
- Hard-coding one consumer for a resource when multiple consumers are expected.
- Reintroducing Python formulas for per-level worker bonuses that belong in
  building JSON.
