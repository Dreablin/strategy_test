# Worker Effects Guide

This file is the coding-agent contract for worker stat modifiers.

## Core Model

Worker stat effects are additive deltas applied to a base multiplier of `1.0`.

- `0.05` means `+5%`.
- `-0.10` means `-10%`.
- Effective multiplier is `1.0 + sum(deltas)`, clamped by `Characteristics`.
- `move_speed_mult` changes tile travel time:

```python
tile_travel_ms = game_settings.timing.worker_tile_travel_ms / move_speed_mult
```

## Supported Stats

The supported stat keys are registered in `config.WORKER_EFFECT_STATS`.

- `move_speed_mult`: movement speed multiplier.
- `gather_speed_mult`: gather/action speed multiplier for gatherer-style work.

When adding a new stat:

- register it in `WORKER_EFFECT_STATS`;
- validate it through `building_worker_effects()`;
- use it in the relevant worker runtime;
- add focused tests;
- update this guide.

## Building Assigned-Worker Effects

Building effects live in the owning building JSON:

```json
"worker_effects": {
  "by_level": {
    "1": {"assigned_worker": {}},
    "2": {
      "assigned_worker": {
        "move_speed_mult": 0.05,
        "gather_speed_mult": 0.05
      }
    }
  }
}
```

`assigned_worker` applies only when:

- the worker is assigned through `Worker.assigned_building`;
- `worker.assigned_building is building`;
- the worker manager applies assignment bonuses for that building.

Transport tasks do not create assignment. A carrier carrying resources to or
from a building never receives that building's `assigned_worker` effects.

A worker type may be compatible with several building types (see
`worker_compatible_building_types` in `worker_hiring.py`), but effects still
apply only to the **currently** `assigned_building`. Reassignment swaps which
building JSON drives `assigned_worker` bonuses; there is no stacking of
effects from every compatible site at once.

## Global And Worker-Type Effects

Static global and worker-type effects live in `game_settings.json`:

```json
"workers": {
  "effects": {
    "global": {},
    "by_type": {
      "CARRIER": {
        "move_speed_mult": 0.05
      }
    }
  }
}
```

`global` applies to every worker when the worker is created.
`by_type.<WORKER_TYPE>` applies only to workers with that exact type tag.
These effects are separate from building assignment effects and use separate
characteristic sources, so later reassignment or demolition does not erase them.

Existing workers keep the effects they received at creation time until code
explicitly refreshes them. Use `worker.refresh_configured_effects()` for one
worker or `WorkerManager.refresh_configured_worker_effects()` for all current
workers. Refresh removes the old global/type sources before applying current
settings, so deleting an effect from settings does not leave stale modifiers.

## Implementation Rules

- Read building effects with `config.building_worker_effects(type_tag, level)`.
- Read global/type startup effects with
  `config.configured_worker_effect_sources(worker_type)`.
- Use `config.configured_worker_effect_source_keys(worker_type)` when removing
  or refreshing global/type sources.
- Do not hard-code level formulas in Python when the value is building balance.
- Do not mutate carriers based on `TransportTask.source` or
  `TransportTask.target`.
- Existing local building bonuses are stored on `worker.characteristics` under a
  building-level source and are cleared on reassignment/demolition.
- Runtime changes to configured global/type effects must call the explicit
  refresh method. Do not make reassignment, delivery, or building demolition
  implicitly mutate global/type sources.
