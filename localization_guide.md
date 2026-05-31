# Localization Guide (Phase 29)

Player-facing text lives in locale JSON files under `src/game/settings/locales/`.
Initial supported languages: English (`en.json`) and Russian (`ru.json`).

## JSON shape: flat dotted keys

Locale files use **flat dotted keys** at the top level, not nested objects:

```json
{
  "ui.button.start": "Start",
  "resource.wood": "Wood",
  "research.1.name": "Technology I"
}
```

Flat keys simplify diffing `en` vs `ru`, completeness checks, and grep-based audits.

## Key naming convention

| Prefix | Example | Use |
|--------|---------|-----|
| `ui.button.<name>` | `ui.button.start` | Button labels |
| `ui.common.<name>` | `ui.common.cost` | Shared UI words (Cost, Status, …) |
| `resource.<id>` | `resource.wood` | Resource display names (`id` = lowercased resource id) |
| `worker.<TYPE>` | `worker.CARRIER` | Worker type labels |
| `building.<TYPE>.name` / `.desc` | `building.TOWN_HALL.name` | Building panel copy |
| `status.<id>` | `status.ready` | Production / worker status text |
| `research.<id>.name` / `.desc` / `.effect` | `research.1.name` | Research display copy |
| `statue.stage.<n>` | `statue.stage.1` | Statue construction stage names (n = 1..4) |
| `ui.lock.<id>` | `ui.lock.no_laboratory` | Research eligibility / lock messages shown in UI |

**Lock reasons:** eligibility code builds messages via `game.lock_reasons` helpers that call `ui.lock.*` keys. Dependency names reuse localized `research.<id>.name` values.

**Ids and enums never change** — only displayed text moves to locales.

## Placeholder syntax

Templates use Python `str.format` placeholders: `{param}`.

```json
{
  "ui.topbar.population": "{current} (max {max})"
}
```

Call site: `t("ui.topbar.population", current=12, max=20)`.

Counts use a `label: N` pattern (e.g. `Wood: 34` / `Дерево: 34`). No grammatical pluralization.

## Fallback chain

When resolving `t(key)`:

1. Look up the key in the **active locale** (default `en`, switchable via `i18n.set_locale`).
2. If missing and locale is not `en`, fall back to **`en`**.
3. If still missing, return the **key id** unchanged (loud failure for tests and dev).

Missing `{param}` values: return the unformatted template rather than raising.

## Runtime entry point

All player-facing strings render through `game.i18n.t(key, **params)` (implemented in T441).
Do not re-introduce raw literals in UI modules once migrated.

## Tests

- Schema / completeness: `tests/test_i18n_schema.py`, `tests/test_locale_completeness.py`
- Loader behavior: `tests/test_i18n_loader.py`
- Locale switching in tests: use the `use_locale` harness in `tests/conftest.py` (T442)

Default test locale is `en` unless a test explicitly switches via the harness.
