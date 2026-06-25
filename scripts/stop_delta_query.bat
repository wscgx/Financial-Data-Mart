@echo off
echo ========================================
echo 停止 Delta Lake 查询服务
echo ========================================

cd /d "%~dp0..\docker"

echo.
echo 停止 Jupyter 和 Spark 服务...
docker-compose stop jupyter spark-worker spark-master

echo.
echo ========================================
echo 服务已停止
echo ========================================

pause
