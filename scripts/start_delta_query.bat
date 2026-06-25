@echo off
echo ========================================
echo 启动 Delta Lake 查询服务
echo ========================================

cd /d "%~dp0..\docker"

echo.
echo [1/3] 启动 Spark 集群...
docker-compose up -d spark-master spark-worker

echo.
echo [2/3] 启动 Jupyter Notebook...
docker-compose up -d jupyter

echo.
echo [3/3] 等待服务启动...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo Spark Master UI:  http://localhost:8080
echo Jupyter Notebook: http://localhost:8888 (Token: datalake)
echo.
echo 使用方式：
echo   1. 浏览器打开 http://localhost:8888
echo   2. 输入 Token: datalake
echo   3. 打开 delta_query_examples.ipynb 开始查询
echo.
echo 或使用命令行工具：
echo   python project/scripts/query_delta.py --list
echo   python project/scripts/query_delta.py "SELECT * FROM delta.`s3a://financial-data-lake/ods/ods_customer` LIMIT 10"
echo ========================================

pause
