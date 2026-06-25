# AI Financial Analytics Platform - 大数据版本

## Overview

AI-driven financial data warehouse and analytics platform implementing Agent-based architecture for automated data warehouse development. 基于大数据技术栈的金融数据仓库和分析平台。

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        数据源层                              │
│  MySQL (OLTP)  ←→  Kafka (实时流)  ←→  MinIO (数据湖)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        ETL 层                               │
│  ODS (原始数据) → DWD (明细层) → DWS (汇总层) → ADS (应用层) │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        计算引擎                              │
│  Spark (批处理)  |  Flink (流处理)  |  Spark Streaming      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        存储层                               │
│  Delta Lake (MinIO)  |  MySQL (查询层)                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        应用层                               │
│  Streamlit (看板)  |  Grafana (监控)  |  Jupyter (分析)     │
└─────────────────────────────────────────────────────────────┘
```

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| MySQL | 3306 | 业务数据库 (financial_dw) |
| MinIO Console | 9001 | 数据湖管理界面 |
| MinIO API | 9000 | S3 兼容 API |
| PostgreSQL | 5432 | Airflow 元数据库 |
| Airflow | 8080 | ETL 调度 UI |
| Kafka | 9092 | 消息队列 |
| Schema Registry | 8081 | Schema 管理 |
| Flink | 8082 | 流处理引擎 |
| Spark UI | 8083 | Spark 作业监控 |
| Jupyter | 8888 | 交互式分析 |
| Prometheus | 9090 | 监控指标 |
| Grafana | 3000 | 监控可视化 |

## Quick Start

### 一键启动 (推荐)

```bash
# Windows
.\启动大数据平台.bat

# 或手动启动
cd project/docker
docker compose up -d
```

### 验证服务

```bash
# 查看服务状态
docker compose ps

# 访问各服务
# Streamlit:  http://localhost:8501
# Spark UI:   http://localhost:8083
# Jupyter:    http://localhost:8888
# MinIO:      http://localhost:9001 (minioadmin/minioadmin)
# Airflow:    http://localhost:8080 (admin/admin)
# Flink:      http://localhost:8082
# Grafana:    http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### 初始化数据

```bash
# 安装 Python 依赖
pip install -r requirements_bigdata.txt

# 执行 ETL 初始化
cd project
python scripts/run_all_etl.py

# 或使用 PySpark 版本 (Delta Lake)
spark-submit etl/spark/etl_ods_to_delta.py
spark-submit etl/spark/etl_dwd_to_delta.py
spark-submit etl/spark/etl_dws_to_delta.py
spark-submit etl/spark/etl_ads_to_delta.py
spark-submit etl/spark/etl_ads_sync_mysql.py
```

## Project Structure

```
Financial Data Mart/
├── .env                              # 环境变量
├── 启动大数据平台.bat                  # 一键启动
├── 停止大数据平台.bat                  # 一键停止
├── 大数据技术栈迁移计划.md             # 迁移计划
├── 大数据技术栈优化完成.md             # 优化完成文档
├── 大数据平台快速参考.md               # 快速参考
└── project/
    ├── app.py                        # Streamlit 入口
    ├── configs/
    │   └── spark_config.py           # Spark/MinIO/Delta/Kafka 配置
    ├── docker/
    │   ├── docker-compose.yml        # Docker 服务编排
    │   ├── .env                      # 环境变量
    │   ├── airflow/
    │   │   ├── dags/
    │   │   │   ├── financial_etl_dag.py
    │   │   │   └── financial_etl_dag_delta.py
    │   │   └── requirements.txt
    │   └── monitoring/
    │       ├── prometheus.yml
    │       └── grafana/provisioning/
    ├── etl/
    │   ├── spark/
    │   │   ├── common.py
    │   │   ├── etl_ods_to_delta.py
    │   │   ├── etl_dwd_to_delta.py
    │   │   ├── etl_dwd_customer_asset_daily.py
    │   │   ├── etl_dws_to_delta.py
    │   │   ├── etl_dws_customer_value_profile.py
    │   │   ├── etl_ads_to_delta.py
    │   │   └── etl_ads_sync_mysql.py
    │   └── *.sql
    ├── streaming/
    │   ├── kafka_producer.py
    │   ├── flink_realtime_agg.py
    │   ├── spark_streaming_agg.py
    │   └── schemas/
    ├── scripts/
    │   ├── run_all_etl.py
    │   ├── etl_metrics_exporter.py
    │   └── run_quality_validation.py
    └── dashboards/
```

## Data Warehouse Layers

- **ODS**: Operational Data Store (6 tables) - 原始数据层
- **DWD**: Data Warehouse Detail (4 tables) - 明细层
- **DWS**: Data Warehouse Summary (5 tables) - 汇总层
- **ADS**: Application Data Store (8 tables) - 应用层

## ETL Pipeline

### 批处理 ETL (每日执行)

```
MySQL ODS → Delta Lake ODS → Delta Lake DWD → Delta Lake DWS → Delta Lake ADS → MySQL ADS
```

### 实时流处理

```
Kafka → Flink/Spark Streaming → Delta Lake → MySQL
```

## Business Domains

- **客户域**: 客户资产、客户行为、客户价值
- **产品域**: 产品销售、产品业绩
- **交易域**: 交易明细、交易汇总
- **资产域**: 资产快照、资产变动
- **风险域**: 风险匹配、风险预警

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| MySQL | 8.0 | OLTP 查询层 |
| MinIO | latest | S3 兼容对象存储 |
| PostgreSQL | 15 | Airflow 元数据库 |
| Airflow | 2.9.3 | ETL 调度编排 |
| Kafka | 7.5.0 | 消息队列 |
| Schema Registry | 7.5.0 | Schema 管理 |
| Flink | 1.18 | 流处理引擎 |
| Spark | 3.5 | 批处理/流处理引擎 |
| Jupyter | latest | 交互式分析 |
| Prometheus | latest | 指标采集 |
| Grafana | latest | 监控可视化 |
| Delta Lake | 3.0.0 | 数据湖格式 |
| Streamlit | latest | 数据看板 |

## Monitoring

### Grafana Dashboard

- **ETL 监控面板**: 任务总数、成功/失败数、处理行数
- **实时流处理监控**: Kafka 消息数、Flink 作业状态
- **系统资源监控**: CPU、内存、磁盘使用率

### Prometheus Metrics

- `etl_task_total`: ETL 任务总数
- `etl_task_success`: ETL 任务成功数
- `etl_task_failed`: ETL 任务失败数
- `etl_rows_processed_total`: ETL 处理总行数
- `mysql_connection_status`: MySQL 连接状态
- `minio_connection_status`: MinIO 连接状态
- `kafka_messages_total`: Kafka 消息总数

## Getting Started

1. 启动 Docker 服务: `.\启动大数据平台.bat`
2. 配置 Agent 提示词: `agents/` 目录
3. 初始化知识库: `knowledge_base/`
4. 执行 ETL 流水线: `python scripts/run_all_etl.py`
5. 访问 Streamlit 看板: `python app.py`

## Documentation

- [大数据技术栈迁移计划](大数据技术栈迁移计划.md)
- [大数据技术栈优化完成](大数据技术栈优化完成.md)
- [大数据平台快速参考](大数据平台快速参考.md)
