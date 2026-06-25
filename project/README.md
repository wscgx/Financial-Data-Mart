# Financial Data Mart

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-24.0-blue.svg)](https://www.docker.com/)
[![Spark](https://img.shields.io/badge/Apache%20Spark-3.5-orange.svg)](https://spark.apache.org/)

> AI-driven financial data warehouse and analytics platform implementing Agent-based architecture for automated data warehouse development.

## Features

- 🏗️ **Lambda 架构** - 批处理 + 实时流处理双模式
- 📊 **完整数仓分层** - ODS → DWD → DWS → ADS 四层数仓架构
- 🔄 **自动化 ETL** - Airflow 调度 + Spark/Delta Lake 处理
- 📈 **实时监控** - Grafana + Prometheus 全链路监控
- 🤖 **AI Agent** - 多角色 Agent 协作开发数仓
- 🐳 **一键部署** - Docker Compose 容器化编排

## Quick Start

### 1. 克隆项目

```bash
git clone https://github.com/wscgx/Financial-Data-Mart.git
cd Financial-Data-Mart
```

### 2. 启动服务

```bash
cd project/docker
docker compose up -d
```

### 3. 初始化数据

```bash
cd project
pip install -r requirements_bigdata.txt
python scripts/run_all_etl.py
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| Streamlit | http://localhost:8501 | 数据看板 |
| Airflow | http://localhost:8080 | ETL 调度 |
| Spark UI | http://localhost:8083 | 作业监控 |
| Grafana | http://localhost:3000 | 监控可视化 |
| MinIO | http://localhost:9001 | 数据湖管理 |

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

## Data Warehouse Layers

| 层级 | 说明 | 表数量 |
|------|------|--------|
| **ODS** | Operational Data Store - 原始数据层 | 6 |
| **DWD** | Data Warehouse Detail - 明细层 | 4 |
| **DWS** | Data Warehouse Summary - 汇总层 | 5 |
| **ADS** | Application Data Store - 应用层 | 8 |

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | 主要开发语言 |
| MySQL | 8.0 | OLTP 查询层 |
| Spark | 3.5 | 批处理/流处理引擎 |
| Delta Lake | 3.0.0 | 数据湖格式 |
| Kafka | 7.5.0 | 消息队列 |
| Flink | 1.18 | 流处理引擎 |
| Airflow | 2.9.3 | ETL 调度编排 |
| MinIO | latest | S3 兼容对象存储 |
| Streamlit | 1.31+ | 数据看板 |
| Docker | 24.0 | 容器化部署 |

## Project Structure

```
Financial Data Mart/
├── project/
│   ├── app.py                  # Streamlit 入口
│   ├── configs/                # 配置文件
│   ├── docker/                 # Docker 编排
│   │   └── docker-compose.yml
│   ├── etl/                    # ETL 脚本
│   │   ├── *.sql               # SQL 脚本
│   │   └── spark/              # PySpark 脚本
│   ├── sql/                    # DDL 建表语句
│   │   ├── ods/
│   │   ├── dwd/
│   │   ├── dws/
│   │   └── ads/
│   ├── dashboards/             # 可视化看板
│   ├── scripts/                # 工具脚本
│   └── tests/                  # 测试文件
└── scripts/                    # 启动脚本
```

## Business Domains

- **客户域**: 客户资产、客户行为、客户价值
- **产品域**: 产品销售、产品业绩
- **交易域**: 交易明细、交易汇总
- **资产域**: 资产快照、资产变动
- **风险域**: 风险匹配、风险预警

## Contributing

欢迎贡献代码！请查看 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解详情。

## License

本项目采用 [MIT License](../LICENSE) 开源协议。
