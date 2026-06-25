@echo off
cd /d "%~dp0..\project\docker"
docker compose down
echo.
echo Done. Press any key to exit.
pause >nul
