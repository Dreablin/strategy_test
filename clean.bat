@echo off
REM ============================================================
REM  clean.bat — remove the local venv created by run.bat
REM
REM  After this script finishes, NOTHING that run.bat downloaded
REM  remains on your computer. Your system Python is untouched.
REM ============================================================

setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_DIR=.venv"

if not exist "%VENV_DIR%" (
    echo [clean.bat] Nothing to clean. "%VENV_DIR%" does not exist.
    exit /b 0
)

REM Refuse to run while the game is still using files in .venv.
tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2>nul | findstr /I "python.exe" >nul
if not errorlevel 1 (
    echo [clean.bat] WARNING: a python.exe process is still running.
    echo             Close the game window first, then re-run this script.
    exit /b 1
)

echo [clean.bat] Removing %VENV_DIR% ...
rmdir /s /q "%VENV_DIR%"
if errorlevel 1 (
    echo [clean.bat] ERROR: could not remove %VENV_DIR%.
    echo             Make sure no editor / antivirus is locking it.
    exit /b 1
)

REM Optional: clear pytest / ruff caches that ralph-loop may have left.
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"
if exist ".ruff_cache"   rmdir /s /q ".ruff_cache"

echo [clean.bat] Done. Venv, pip cache and tool caches removed.
exit /b 0
