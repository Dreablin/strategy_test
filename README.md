# Isometric Strategy

A lightweight isometric economy strategy game built with Python + Pygame.
Start immediately, place buildings, hire workers, and grow resource income.

## Run from source

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

## Gameplay summary

- Start with a Town Hall and initial resources.
- Build production buildings (Lumber Camp, Stone Mine, Iron Mine, Farm).
- Hire workers from the Town Hall panel; only staffed buildings produce.
- Every 10 seconds, staffed buildings add `5 x level` of their resource.
- Upgrade buildings to increase production; demolish to replan your layout.
