@echo off
cd /d "%~dp0..\project\docker"
docker compose up -d
echo.
echo Done. Press any key to exit.
pause >nul
