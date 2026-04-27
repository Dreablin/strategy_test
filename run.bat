@echo off
REM ============================================================
REM  run.bat — create local venv, install requirements, run game
REM
REM  Everything (venv + pip cache + downloaded wheels) lives in
REM  .\.venv\ next to this script, so clean.bat can wipe it
REM  completely without touching anything else on your machine.
REM ============================================================

setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "FLAG_FILE=%VENV_DIR%\.deps_installed"

REM --- 1. Locate a system Python (3.10+) -----------------------
set "BOOT_PY="
where py >nul 2>nul && (set "BOOT_PY=py -3")
if not defined BOOT_PY (
    where python >nul 2>nul && (set "BOOT_PY=python")
)
if not defined BOOT_PY (
    echo [run.bat] ERROR: no Python interpreter found on PATH.
    echo            Install Python 3.10+ from https://www.python.org/downloads/
    echo            or the Microsoft Store, then re-run this script.
    exit /b 1
)

REM --- 2. Create venv if missing -------------------------------
if not exist "%VENV_PY%" (
    echo [run.bat] Creating virtual environment in %VENV_DIR% ...
    %BOOT_PY% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [run.bat] ERROR: failed to create venv.
        exit /b 1
    )
)

REM --- 3. Force pip cache to live INSIDE the venv --------------
REM     This way clean.bat can erase 100 %% of what was downloaded.
set "PIP_CACHE_DIR=%CD%\%VENV_DIR%\pip-cache"

REM --- 4. Install / update requirements (only on first run or
REM        when requirements.txt is newer than the marker) ------
set "NEED_INSTALL="
if not exist "%FLAG_FILE%" set "NEED_INSTALL=1"
if defined NEED_INSTALL goto :install
for /f %%t in ('powershell -NoProfile -Command "(Get-Item requirements.txt).LastWriteTimeUtc -gt (Get-Item '%FLAG_FILE%').LastWriteTimeUtc"') do (
    if /i "%%t"=="True" set "NEED_INSTALL=1"
)

:install
if defined NEED_INSTALL (
    echo [run.bat] Installing dependencies into %VENV_DIR% ...
    "%VENV_PY%" -m pip install --upgrade pip
    if errorlevel 1 exit /b 1
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 exit /b 1
    > "%FLAG_FILE%" echo installed
)

REM --- 5. Launch the game --------------------------------------
echo [run.bat] Launching game ...
set "PYTHONPATH=%CD%\src"
"%VENV_PY%" -m game.main
set "RC=%ERRORLEVEL%"
echo [run.bat] Game exited with code %RC%.
exit /b %RC%
