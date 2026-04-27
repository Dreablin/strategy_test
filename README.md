# Isometric Strategy

A lightweight isometric economy strategy game built with Python + Pygame.
Start immediately, place buildings, hire workers, and grow resource income.

## Run without polluting your system

Two helper scripts keep everything self-contained inside `.\.venv\`:

- `run.bat`  — creates a local virtual environment on first run, installs the
  required packages into it (with the pip cache redirected to `.venv\pip-cache`),
  then launches the game. Subsequent runs reuse the venv and start instantly.
- `clean.bat` — removes `.venv\` (and `.pytest_cache\` / `.ruff_cache\` if
  present). Nothing the scripts downloaded remains on your machine.

You only need a system Python 3.10+ on `PATH` (or the `py` launcher). No global
`pip install` is performed.

## Run from source manually

Install dependencies and run:

`pip install -r requirements.txt && python -m game.main`

## Build executable

Use the batch script:

`build_exe.bat`

Or run PyInstaller directly:

`pyinstaller --onefile --noconsole -n IsometricStrategy src/game/main.py`

## Controls

- `LMB`: place selected building, or open a building panel.
- `RMB` / `Esc`: cancel placement or close an open panel.
- Building panels now include active toggles for camp/mine workflows and live storage counters.

## Gameplay summary

- Start with a Town Hall and initial resources.
- Build production buildings (Lumber Camp, Stone Mine, Iron Mine, Farm).
- Hire workers from the Town Hall panel; only staffed buildings produce.
- Stonecutters run an active mine cycle (walk, mine, return, deposit) and can be toggled on/off per mine.
- Producing buildings use internal storage caps, so full storage pauses new production until space is freed.
- Worker move/gather speed gains +5% per building level above 1 while assigned to that building.
- Every 10 seconds, staffed buildings add `5 x level` of their resource.
- Upgrade buildings to increase production; demolish to replan your layout.
