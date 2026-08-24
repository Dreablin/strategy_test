# Isometric Strategy

A local experiment in fully automated AI-agent development.

This repository is an educational project exploring how far AI coding agents can
go when working in an autonomous loop with a Spec Driven Development (SDD)
workflow. The game is a lightweight isometric economy strategy prototype built
with Python + Pygame, but the main purpose of the repository is to study the
engineering process: turning specs into implementation, tests, assets, iteration
notes, and runnable builds.

100% of the code and game assets in this repository were generated
automatically through the SDD process. Development is still in progress, so the
project should be read as an active technical experiment rather than a finished
commercial game.

The goal is to keep the experiment practical and inspectable: a recruiter or
engineer should be able to review the repository, run the project locally, and
see a concrete example of AI-assisted autonomous development with tests,
configuration, UI iteration, and game-domain behavior evolving together.

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
