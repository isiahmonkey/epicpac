@echo off
rem Token incremental build. If GarrysMod is installed elsewhere, change the path below.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -GMOD "C:\Program Files (x86)\Steam\steamapps\common\GarrysMod"
pause
