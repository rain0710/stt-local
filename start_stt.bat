@echo off
rem Launch STT Local silently (tray app, no console window).
rem Logs are written to stt_local.log in this folder.
setlocal
set "PYW=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"
start "" "%PYW%" "%~dp0main.py"
endlocal
