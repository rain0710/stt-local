@echo off
rem Launch STT Local with a console window for troubleshooting.
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" main.py
echo.
echo === STT exited. Press any key to close. ===
pause >nul
