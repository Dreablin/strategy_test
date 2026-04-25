@echo off
setlocal

pyinstaller --onefile --noconsole -n IsometricStrategy src/game/main.py

endlocal
