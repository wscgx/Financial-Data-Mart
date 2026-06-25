@echo off
echo.
echo === Docker Services ===
cd /d "%~dp0..\project\docker"
docker compose ps
echo.
echo === Ports Check ===
netstat -ano | findstr "LISTENING" | findstr ":3307 :9000 :9001 :9092 :3000 :9090"
echo.
echo === Service URLs ===
echo MinIO:      http://localhost:9001
echo Grafana:    http://localhost:3000
echo Prometheus: http://localhost:9090
echo MySQL:      localhost:3307
echo.
echo Press any key to exit.
pause >nul
