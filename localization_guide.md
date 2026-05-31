# Localization Guide (Phase 29)

Player-facing text lives in locale JSON files under `src/game/settings/locales/`.
Initial supported languages: English (`en.json`) and Russian (`ru.json`).

See also: [`building_extension_guide.md`](building_extension_guide.md),
[`worker_extension_guide.md`](worker_extension_guide.md),
[`research_extension_guide.md`](research_extension_guide.md).

## Locale folder

```
src/game/settings/locales/
  en.json    # English (default; fallback source)
  ru.json    # Russian
```

- One JSON file per language code (lowercase, e.g. `de.json` for German).
- Files are loaded at runtime by `game.i18n` (`src/game/i18n.py`).
- **Balance and gameplay data stay out of locale files** — construction costs,
  research points, worker timings, etc. remain in `src/game/settings/` JSON.
- After editing any locale file, run `pytest -q tests/test_locale_completeness.py`
  to confirm all languages share the same key set.

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
| `ui.panel.<name>` | `ui.panel.input` | Shared panel phrases |
| `ui.lock.<id>` | `ui.lock.no_laboratory` | Research eligibility / lock messages |
| `resource.<id>` | `resource.wood` | Resource display names (`id` = lowercased resource id) |
| `worker.<TYPE>` | `worker.CARRIER` | Worker type labels |
| `building.<TYPE>.name` / `.desc` | `building.TOWN_HALL.name` | Building panel copy |
| `status.<id>` | `status.ready` | Production / worker status text |
| `research.<id>.name` / `.desc` / `.effect` | `research.1.name` | Research display copy |
| `statue.stage.<n>` | `statue.stage.1` | Statue construction stage names (n = 1..4) |

**Lock reasons:** eligibility code builds messages via `game.lock_reasons` helpers
that call `ui.lock.*` keys. Dependency names reuse localized `research.<id>.name`
values.

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

Unknown resource ids fall back to title-cased id text in `resource_display_label()`
(e.g. `mystery_ore` → `Mystery Ore`) — add a `resource.*` key when the resource is
player-facing.

## Runtime entry point

All player-facing strings render through `game.i18n.t(key, **params)` (implemented in T441).
Do not re-introduce raw literals in UI modules once migrated.

```python
from game import i18n

label = i18n.t("ui.button.start")
line = i18n.t("ui.topbar.population", current=3, max=8)
```

Switch locale at runtime (settings menu, tests):

```python
i18n.set_locale("ru")
i18n.get_locale()  # current code
```

## Adding a new language

1. **Copy the key set from `en.json`** into `src/game/settings/locales/<code>.json`
   (e.g. `de.json`). Keep keys identical; translate values only.
2. **Translate every value.** Empty or whitespace-only strings fail
   `tests/test_locale_completeness.py`.
3. **Run completeness and loader tests:**

   ```powershell
   $env:PYTHONPATH='src'
   pytest -q tests/test_locale_completeness.py tests/test_i18n_loader.py
   ```

4. **Add RU-style layout smoke tests** if the new script is significantly wider
   than English (see `tests/test_locale_ru_layout.py` as a template).
5. **Wire locale selection** in game settings / options UI when product-ready
   (`i18n.set_locale(code)` on change). Until then, tests can exercise the catalog
   via the harness below.
6. **No code changes are required** for lookup once the JSON file exists — `i18n`
   loads files lazily by locale code.

When adding keys for a new building, worker, or research entry, add them to **all**
locale files in the same commit.

## Tests

Default test locale is **`en`**. An autouse fixture in `tests/conftest.py` resets
locale to `en` after every test to prevent leakage under `pytest-xdist`.

### Locale harness (T442)

Use the `use_locale` fixture to exercise non-English copy:

```python
def test_panel_title_ru(use_locale) -> None:
    with use_locale("ru"):
        assert i18n.t("building.TOWN_HALL.name") != "building.TOWN_HALL.name"
```

The fixture returns a context manager factory; nested switches restore the previous
locale on exit.

### Test expectations

| Area | What to assert | Avoid |
|------|----------------|-------|
| UI labels | `i18n.t("ui....")` or helper that calls `t()` | Hardcoded `"Upgrade"`, `"Лагерь…"` |
| Building names | `building_display_name("TAG")` or `i18n.t("building.TAG.name")` | Literal building titles |
| Resources | `resource_display_label("wood")` or `i18n.t("resource.wood")` | Literal resource names |
| Workers | `worker_display_label("CARRIER")` or `i18n.t("worker.CARRIER")` | Literal worker titles |
| Lock reasons | `lock_reason_*()` helpers from `game.lock_reasons` | English eligibility strings |
| RU smoke | `with use_locale("ru"):` block | Assuming Russian in default `en` tests |

**Loader / harness tests** (`test_i18n_loader.py`, `test_i18n_harness.py`) may
compare against known `en`/`ru` strings — that is intentional.

### Test modules

- Schema / completeness: `tests/test_i18n_schema.py`, `tests/test_locale_completeness.py`
- Loader behavior: `tests/test_i18n_loader.py`
- RU layout overflow: `tests/test_locale_ru_layout.py`
- Locale switching: `tests/test_i18n_harness.py`, `tests/conftest.py` (`use_locale`)

Run before marking localization work done:

```powershell
$env:PYTHONPATH='src'
python -c "import game.i18n"
pytest -q
```

## Literal allowlist (T464 audit)

The following are **intentionally not** in locale JSON. Do not migrate them without a product reason.

| Location | What stays English / internal | Why |
|----------|------------------------------|-----|
| `src/game/dev_asset_reload.py` | `"Reload"` button label | Dev-only hot-reload tool; module is removable |
| UI click/action return values | `"close"`, `"upgrade"`, `"hire:CARRIER"`, menu keys `"resource"` / `"food"` | Internal action tokens, not rendered copy |
| `canteen_panel.py` | `diner.type_tag[:3]` abbreviations | Compact row tags; full worker names use `worker.*` elsewhere |
| Building / worker type tags | `LUMBER_CAMP`, `CARRIER`, … | Stable ids; display names come from `building.*` / `worker.*` keys |
| `ValueError` / `assert` messages | Exception text in loaders and registries | Developer diagnostics, not player UI |
| Docstrings and module `__doc__` | English prose | Not shown in-game |
| Log / debug strings | Any `print` or future logging | Not player-facing |

When adding new UI copy, default to a new `ui.*`, `resource.*`, `building.*`, or `status.*` key rather than expanding this list.
