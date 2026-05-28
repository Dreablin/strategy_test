# Laboratory and Research Extension Guide

This file is the coding-agent contract for the Phase 28 Laboratory building,
`SCIENTIST` worker, and the research system. Product goals and acceptance rules
are summarized in **`progress.md`** (Phase 28 design notes). **`PRD.md`** is the
long-term product contract; do not edit it from the Ralph loop—mirror any PRD
updates here when implementation touchpoints change.

## Core Rules

- **One Laboratory** may exist or be under construction at a time
  (`BuildingRegistry.place` enforces this).
- **One active research** at a time; starts are not cancellable by the player.
- **Research data is JSON-driven** (`src/game/settings/research.json`). Do not
  hard-code dependency chains, costs, or tier layout in Python except for the
  static Technology id list used in `research_technology_chain.py`.
- **Balance numbers live in JSON** (research costs/points, Laboratory slots,
  points-per-second, tier unlock levels). Tests should assert behavior and
  schema, not exact balance values.
- **Dynamic Laboratory input storage** exists only while a research is active.
  Panel UI shows **real delivered amounts only**—not queued or in-flight cargo.
- **Research points** accrue only after every required resource is delivered to
  that storage. Carriers use purpose `"laboratory_research"`.
- **Completed research effects** must be schema-driven. Worker characteristic
  bonuses use `worker_effects.by_type` in `research.json`; other effect families
  need an explicit schema/design before implementation.

## Configuration and Assets

| What | Where |
|------|--------|
| Research definitions | `src/game/settings/research.json` |
| Loader / `RESEARCH_BY_ID` | `src/game/research_config.py` |
| Completed worker effects | `worker_effects.by_type` in research JSON + `src/game/research_effects.py` |
| Laboratory balance | `src/game/settings/buildings/laboratory.json` |
| Scientist tier / hire cap | `game_settings.json` (`workers.tiers`, hire limits) |
| Research images (disk) | `assets/research/<image_key>.png` |
| Research image resolver | `src/game/research_assets.py` |
| Laboratory building sprites | `assets/buildings/laboratory/` (+ `assets.py` mapping) |

### Adding a research entry

1. Add an object to `research.json` `researches` with: `id`, `name`,
   `description`, `effect_text`, `tier` (1–4), `column`, `dependencies`,
   `resource_cost`, `required_points`, `image_key`.
   `effect_text` is the player-facing tooltip line after `Effect:`.
   Optional worker-characteristic effects belong under:
   `"worker_effects": {"by_type": {"CARRIER": {"move_speed_mult": 0.1}}}`.
   Supported stat keys are the same worker characteristic keys used by building
   level effects.
2. Add a placeholder PNG at `assets/research/<image_key>.png` (or rely on
   procedural fallback from `research_assets.py`).
3. Loader validation runs at import time in `research_config.py`—fix any
   duplicate ids, bad tiers, or broken dependency references before tests run.
4. **Technology researches** use ids `"1"`–`"4"`, `column: 0`, tier matches row,
   and chain dependencies (`"2"` depends on `"1"`, etc.). Laboratory **level**
   gates tier availability via `technology_tiers.unlock_level_by_tier` in
   `laboratory.json` (not in research JSON).
5. For non-Technology researches, use `dependencies` only—do not add Python
   chain tables. Eligibility uses `research_eligibility.missing_research_dependencies`.

## Domain Runtime (no UI)

| Module | Role |
|--------|------|
| `research_state.py` | In-memory run state: completed ids, active id, delivered map, points |
| `research_start.py` | `try_start_active_research` — eligibility + init lab storage |
| `research_eligibility.py` | Start gates: lab present, not completed, no active research, tier, deps |
| `research_technology_chain.py` | Technology id helpers; delegates eligibility to registry |
| `research_point_production.py` | Points only when inputs delivered; per-lab tick timestamps |
| `research_completion.py` | `try_complete_active_research` when points ≥ requirement |
| `research_effects.py` | Completed research worker-effect source keys and effect lookup |
| `laboratory_visibility.py` | `has_completed_laboratory` / `completed_laboratory` for gating |
| `buildings/laboratory.py` | Slot capacity, tier unlock helpers, dynamic input storage API |

**Shared state:** `GameInput` and `WorkerManager` must use the **same**
`ResearchState` instance when testing or wiring transport/points (see
`tests/test_laboratory_research_integration.py`).

### Start → deliver → points → complete

1. **Start:** `try_start_active_research` or Research screen Start click →
   `research_state.start_research` + `laboratory.initialize_research_input_storage`.
2. **Deliver:** `transport_tasks.laboratory_input_transport_tasks` plans normal
   carrier tasks into the Laboratory: warehouse resources come from Town Hall,
   and `water` comes from completed Wells with local stock. `worker_transport`
   delivers with purpose
   `"laboratory_research"` and calls `_record_laboratory_research_delivery` to
   sync `ResearchState` delivered amounts. Inbound counts prevent overfill.
3. **Gate:** `laboratory.all_research_inputs_delivered()` before points.
4. **Points:** `WorkerManager._update_laboratory_research_points` →
   `tick_laboratory_research_points` using
   `laboratory_research_contributing_scientist_count` (inside footprint, not
   dining/idle).
5. **Complete:** `try_complete_active_research` clears active research and lab
   storage; marks id completed.

### Demolition / invalidation

- Demolishing the Laboratory while research is active:
  `ResearchState.cancel_active_research()`, clear input storage, release
  Scientists (`workers.release_laboratory_scientists`), reroute carriers per
  existing invalid-delivery rules (`worker_transport`).

## Laboratory Building

- **Class:** `src/game/buildings/laboratory.py`, `type_tag = "LABORATORY"`.
- **Menu:** Social category in `ui/bottom_bar.py`.
- **Uniqueness:** `buildings/registry.py` blocks a second Laboratory.
- **Staffing:** Multi-slot Scientists—not the normal one-worker model. Slot
  counts come from `scientist_slots.capacity_by_level` in `laboratory.json`.
- **Panel:** `ui/laboratory_panel.py` + `ui/laboratory_panel_research.py`
  (slots, active research image, input lines, progress bar `350 / 5000`).
- **Construction:** Standard `ConstructionSite`; Scientists paused while
  `is_under_construction` (`pause_laboratory_scientists`).

See **`building_extension_guide.md`** (Laboratory section) for placement, assets,
and transport pointers.

## Scientist Worker

- **Type:** `SCIENTIST`, **tier:** `advanced` (`game_settings.json`).
- **School:** Advanced tab via `worker_tier()` — `ui/school_panel.py`.
- **Compatibility:** `LABORATORY` only (`worker_hiring.WORKER_TO_BUILDING` and
  `worker_laboratory.scientist_compatible_with_building`).
- **Assignment:** `WorkerManager.reassign_all` fills free Laboratory slots up to
  `scientist_slot_capacity()` (see `workers.py` SCIENTIST branch).
- **Contribution rules:** `worker_laboratory.scientist_contributes_to_research_points`
  (assigned, inside footprint, not dining/idle).
- **Status strings:** `worker_status.py` Laboratory / Scientist branches.

See **`worker_extension_guide.md`** (Scientist section).

## Research UI

| Piece | Module |
|-------|--------|
| Top-bar button visibility | `ui/top_bar.py` — `research_button_visible(registry)` |
| Open/close screen | `input.py` — `_research_screen_open`, Esc/close |
| Full-screen layout | `ui/research_screen.py`, `research_screen_layout.py` |
| Tiles | `research_tiles.py`, `research_tile_layout.py`, `research_tile_visual.py` |
| Start buttons | `research_start_button.py` — wired to eligibility + `try_start_active_research` |
| Tooltips | `research_tile_tooltip.py` |
| Button refresh on lab lifecycle | `input._sync_research_ui_state`, `main.py` top bar |

Eligibility for drawing: `research_ui_eligibility` in `research_eligibility.py`.

## Transport Integration

- **Planner:** `transport_tasks.laboratory_input_transport_tasks(registry, inbound_counts=...)`
  — Town Hall warehouse resources plus `water` from Well local storage.
- **Enqueue:** `WorkerManager.update` → `_enqueue_laboratory_research_input_tasks`
  in `worker_transport.py` (deduped with other transport).
- **Purpose:** `"laboratory_research"` on `TransportTask`.
- **Delivery:** Deposit into `laboratory.add_research_input`; sync research state.
- **Capacity:** Count inbound queued/carried units so dynamic storage is not overfilled.

Do not add Laboratory delivery logic on the building class—keep it in
`transport_tasks.py` / `worker_transport.py`.

## Tests to Use as Templates

- Config/schema: `tests/test_research_config*.py`, `tests/test_research_json.py`
- Eligibility / chain: `tests/test_research_eligibility*.py`,
  `tests/test_research_technology_chain_unlock.py`
- Transport: `tests/test_laboratory_research_delivery.py`,
  `tests/test_research_resources_delivered_gate.py`
- Points / scientists: `tests/test_research_point_production_*.py`,
  `tests/test_research_scientist_contribution.py`
- UI: `tests/test_research_screen.py`, `tests/test_research_tile_*.py`,
  `tests/test_top_bar_research_button_refresh.py`
- End-to-end: `tests/test_laboratory_research_integration.py`

Before marking a task done:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check src tests
```

## Avoid

- Hard-coding Technology dependency chains outside `research.json` (except the
  documented `TECHNOLOGY_IDS` helper for the four static tiers).
- Showing in-flight carrier amounts in Laboratory or Research tile storage UI.
- Letting `WorkerManager` and `GameInput` use different `ResearchState` instances.
- Using passive `Building.income()` for research resources or points.
- Adding a second Laboratory without revisiting registry uniqueness and UI gates.
- Implementing ad-hoc per-research gameplay bonuses outside a documented effect schema.
