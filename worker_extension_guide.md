# Worker Extension Guide

This file is the coding-agent contract for adding new worker types without
growing `src/game/workers.py` back into a monolith.

## Core Rule

`src/game/workers.py` is a coordinator and compatibility facade. Keep it focused
on worker storage, assignment/reassignment, demolition cleanup, the frame update
loop, shared approach/parking helpers, and shared building bonuses.

Do not put new worker state machines directly in `workers.py`. Add runtime code
to the focused worker module that matches the worker's behavior.

## Current Worker Modules

- `worker_models.py`: `Worker`, `TransportTask`, and worker characteristics.
- `worker_constants.py`: worker timing, speed, and retry constants.
- `worker_hiring.py`: school hiring lists, worker-to-building mapping, housing
  checks, and hire helpers.
- `worker_status.py`: panel/status/progress text helpers.
- `worker_transport.py`: carrier transport queue and delivery runtime.
- `worker_building.py`: builder runtime.
- `worker_farming.py`: farmer and field runtime.
- `worker_gathering.py`: lumberjack, stonecutter, forester, miner, gather
  targeting, and return-to-camp runtime.
- `worker_processing.py`: indoor processing workers using `ProcessorSpec`.
- `transport_tasks.py`: task builders that enqueue resource movement.
- `worker_geometry.py`: shared small geometry helpers.

## Adding a New Worker

1. Define the worker identity.

   - Add the worker type to `HIRABLE_WORKERS` in `worker_hiring.py`.
   - Map it in `WORKER_TO_BUILDING` if it staffs a building.
   - Add school UI/icon data where school hiring controls are built.
   - Add or verify worker assets and asset loading tests.

2. Decide the runtime category.

   - Carrier-like delivery: extend `worker_transport.py`.
   - Builder-like construction: extend `worker_building.py`.
   - Field/crop work outside a farm: extend `worker_farming.py`.
   - World resource gathering or planting: extend `worker_gathering.py`.
   - Indoor input-to-output processing: prefer `ProcessorSpec` in
     `worker_processing.py`.
   - Truly new behavior: create a focused `worker_<domain>.py` mixin instead of
     adding a large method to `workers.py`.

3. Wire the updater only in `WorkerManager.__init__`.

   Add one `_updaters` entry such as:

   ```python
   "NEW_WORKER": self._update_new_worker,
   ```

   If a new mixin is needed, import it in `workers.py` and add it to
   `WorkerManager` inheritance. Keep the mixin method name private and
   behavior-specific.

4. Keep building and worker contracts capability-based.

   Prefer methods such as `input_amount()`, `output_amount()`,
   `input_capacity()`, `output_capacity()`, `add_<resource>_in()`,
   `take_<resource>_in()`, and `add_<resource>_out()` over hard-coded
   `resource -> building type` tables. Add a hard-coded mapping only when the
   gameplay rule is genuinely type-specific.

5. Keep transport separate from production.

   Production workers should update local building storage only. Carrier
   delivery needs should be expressed through `transport_tasks.py` and
   `worker_transport.py`, not hidden inside processing/gathering state machines.

6. Preserve lifecycle cleanup.

   Check demolition, reassignment, reservation release, and storage-full waits.
   If the worker reserves a tile/resource/building, add explicit release logic
   on completion, cancellation, demolition, and target disappearance.

## Transport Queue Rules

Carrier delivery is a shared system, not part of individual worker production
logic.

- Put desired delivery generation in `transport_tasks.py`. These functions
  should describe what deliveries are needed from current world state.
- Put queue selection, deduplication, carrier state transitions, invalid-task
  rerouting, and carried-resource return/drop behavior in `worker_transport.py`.
- Count real local storage separately from inbound work. Player panels should
  show actual stored amounts only, while queue logic must count queued and
  already-carried resources to avoid overfilling targets.
- Use `_inbound_resource_count()` / related helpers when adding capacity checks
  for a resource or building input.
- If a target/source building is demolished while a carrier is en route, normal
  resources should be rerouted back to Town Hall. Water is not stored in Town
  Hall and should be dropped/cleared.
- Water tasks are special: carriers reserve a free `WELL`, draw water there,
  release the well after leaving with water, and deliver directly to the
  consumer.
- If a task cannot be assigned because a temporary source is busy, do not block
  unrelated tasks behind it. Requeue or skip it so other eligible deliveries can
  proceed.

## Adding a Worker-Operated Building

- Add the building class/config/settings/assets/menu/panel pieces in the normal
  building modules.
- Completed work buildings should start unstaffed. Let
  `WorkerManager.reassign_all()` assign an idle compatible worker.
- If the building processes inputs into outputs, use `ProcessorSpec` unless its
  cycle is materially different.
- If the building needs carrier-delivered inputs or exported outputs, add or
  extend transport task builders in `transport_tasks.py`.
- Do not use passive `Building.income()` for active resources.

## Tests to Add or Update

Use focused tests first, then run the full suite.

- Hiring/school tests for worker availability, queue behavior, icons, and
  housing gates.
- Runtime tests for the worker state machine and timing.
- Demolition/reassignment tests if the worker can be mid-task.
- Transport tests when local storage, direct delivery, water, or inbound counts
  are involved.
- Panel/status/progress tests when the player-visible state changes.
- Asset tests for new worker/building sprites and JSON metadata.

Before marking a task done, run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest
```

## Avoid

- Adding another long worker runtime directly to `workers.py`.
- Duplicating a processor cycle instead of extending `ProcessorSpec`.
- Reintroducing passive wallet income or direct Town Hall hiring.
- Hard-coding one consumer for a resource if more consumers are expected.
- Mixing carrier queue decisions into production worker code.
- Reusing special-case logic for `FIELD`, `WELL`, or `TOWN_HALL` as if they
  were normal buildings.
