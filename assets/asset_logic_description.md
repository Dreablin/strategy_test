# Asset Structure Description

This document describes the canonical asset folder structure for this project.
It is intended for future coding-agent work and should be treated as the source
of truth for where game art assets must be placed.

## Root

- `assets/`
  - Main folder for all art/content files used by the game.

## Buildings

- `assets/buildings/`
  - Contains one subfolder per building type.

Current building folders:

- `assets/buildings/town_hall/`
- `assets/buildings/lumber_camp/`
- `assets/buildings/stone_mine/`
- `assets/buildings/iron_mine/`
- `assets/buildings/farm/`
- `assets/buildings/forester_hut/`
- `assets/buildings/sawmill/`
- `assets/buildings/windmill/`
- `assets/buildings/bakery/`
- `assets/buildings/chicken_farm/`
- `assets/buildings/school/`
- `assets/buildings/house/`
- `assets/buildings/well/`

## NPC

- `assets/npc/`
  - Contains one subfolder per worker/unit type.

Current NPC folders:

- `assets/npc/lumberjack/`
- `assets/npc/stonecutter/`
- `assets/npc/miner/`
- `assets/npc/farmer/`
- `assets/npc/animal_herder/`

## Naming and mapping rules

- Folder names are lowercase snake_case.
- Building folder names map to building `type_tag` values:
  - `TOWN_HALL -> town_hall`
  - `LUMBER_CAMP -> lumber_camp`
  - `STONE_MINE -> stone_mine`
  - `IRON_MINE -> iron_mine`
  - `FARM -> farm`
  - `FORESTER_HUT -> forester_hut`
  - `SAWMILL -> sawmill`
  - `MILL -> windmill`
  - `BAKERY -> bakery`
  - `CHICKEN_FARM -> chicken_farm`
  - `SCHOOL -> school`
  - `HOUSE -> house`
  - `WELL -> well`
- NPC folder names map to worker type values:
  - `LUMBERJACK -> lumberjack`
  - `STONECUTTER -> stonecutter`
  - `MINER -> miner`
  - `FARMER -> farmer`
  - `ANIMAL_HERDER -> animal_herder`

## Required filenames (active loader contract)

The runtime loader in `src/game/assets.py` already reads files from this
structure. You can replace files in place and the game will use them.

### Buildings

Inside each `assets/buildings/<building_name>/` folder:

- `default.png` (optional, fallback)
- `level_01.png` ... `level_10.png` (optional per level)
- `asset_meta.json` (optional, one file per building folder)

Load order for a building of level `L`:

1. `level_XX.png` (`XX` is zero-padded, e.g. `level_03.png`)
2. `level_L.png` (non-padded legacy form, e.g. `level_3.png`)
3. `default.png`
4. procedural fallback from code (if no file exists)

`asset_meta.json` schema (one file for the whole building, not per image):

```json
{
  "default": {
    "scale": 1.0,
    "anchor_norm": [0.5, 1.0]
  },
  "levels": {
    "1": { "scale": 0.8 },
    "10": { "anchor_norm": [0.5, 0.94] }
  }
}
```

- `default` applies to all levels.
- `levels` overrides selected levels (`"1"` or `"01"` forms are accepted).
- `scale` rescales the loaded PNG at runtime.
- `anchor_norm` is normalized anchor coordinates in range `[0..1]`:
  - `x=0` left edge, `x=1` right edge
  - `y=0` top edge, `y=1` bottom edge
- Optional alternative: `anchor_px` in source-image pixels.

### What anchor means

The renderer places each building by matching:

- **world point:** bottom-center of the building footprint on the map,
- **sprite point:** anchor from metadata.

So the anchor is literally “which pixel inside the sprite sits on the tile
contact point”.

How to choose quickly:

1. Find the pixel where the building visually touches the ground in the middle.
2. Set that as anchor (`anchor_norm` or `anchor_px`).
3. Adjust `scale` until footprint feels correct relative to tiles.

### NPC

Inside each `assets/npc/<unit_name>/` folder:

- `default.png` (worker icon / sprite)

Load order:

1. `default.png`
2. procedural fallback from code

## Icons (Hire UI)

- `assets/icons/workers/`
  - `<worker_type>.png` files:
    - `lumberjack.png`
    - `stonecutter.png`
    - `miner.png`
    - `farmer.png`
    - `animal_herder.png`
- `assets/icons/hire/`
  - `<worker_type>.png` files (hire/action icon for each worker type):
    - `lumberjack.png`
    - `stonecutter.png`
    - `miner.png`
    - `farmer.png`
    - `animal_herder.png`

Runtime behavior:

- Town Hall hire buttons are icon-based and auto-scale icons to fixed sizes in UI.
- Icon PNG source resolution can vary; runtime scales to button slot size.
- If an icon file is missing, code uses procedural fallback icons.

## Current seeded files

- Placeholder PNG files are already generated for all building folders:
  - `default.png`
  - `level_01.png` ... `level_10.png`
- Placeholder PNG files are already generated for all NPC folders:
  - `default.png`
