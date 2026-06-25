# 传统数仓 vs 湖仓一体架构对比

## 一、当前项目架构（传统数仓）

```
CSV文件 → ODS → DWD → DWS → ADS → Streamlit前端
         (MySQL)   (MySQL)   (MySQL)   (MySQL)
```

### 特点
- **存储**：所有数据都在 MySQL 单机数据库
- **计算**：纯 SQL ETL 脚本，无调度编排
- **数据格式**：CSV 原始文件 → MySQL 行存储
- **处理模式**：全量刷新（INSERT IGNORE / INSERT OR REPLACE）
- **无历史版本**：数据覆盖写入，无法追溯历史状态

---

## 二、湖仓一体架构（Lakehouse）

```
原始数据 → 湖仓存储层 → 湖仓计算层 → 应用层
(Any)     (Data Lake)    (Lakehouse)   (BI/ML)
          Delta Lake/    Spark/Flink/
          Iceberg/Hudi   Trino/Presto
```

### 核心理念
在廉价的对象存储（如 S3/HDFS/MinIO）上，通过表格式（Table Format）实现数仓级别的 ACID 事务和性能。

---

## 三、逐维度对比

| 维度 | 当前项目 | 湖仓一体 |
|---|---|---|
| **存储介质** | MySQL 磁盘 | S3/HDFS/MinIO 对象存储 |
| **数据格式** | MySQL 行存储 | Parquet/ORC 列式存储 |
| **表格式** | 无 | Delta Lake / Iceberg / Hudi |
| **ACID 事务** | 依赖 MySQL 引擎 | 表格式原生支持 |
| **Schema 管理** | DDL 定义，手动维护 | Schema Evolution，自动演进 |
| **历史版本** | 不支持（覆盖写） | Time Travel，可回溯任意时间点 |
| **数据更新** | INSERT OR REPLACE（全量） | MERGE/UPSERT（增量） |
| **计算引擎** | MySQL 查询 | Spark / Flink / Trino |
| **流批一体** | 不支持 | Flink 流 + Spark 批统一 |
| **成本** | MySQL 存储成本高 | 对象存储成本极低（1/10） |
| **数据湖兼容** | 不支持 | 原生支持 Parquet/ORC |

---

## 四、举例说明

### 例子1：数据更新（当前 vs 湖仓）

#### 当前项目（全量覆盖）
```sql
-- etl_dwd_customer_asset_daily.sql
INSERT IGNORE INTO dwd_customer_asset_daily ...
-- 或者
INSERT OR REPLACE INTO dwd_product_sales_daily ...
-- 问题：每天跑完，前一天的数据被覆盖，无法回溯
```

#### 湖仓一体（增量更新 + 版本控制）
```python
# Delta Lake 示例
from delta.tables import DeltaTable

# 增量合并（只更新变化的数据）
delta_table = DeltaTable.forPath(spark, "s3://lake/dwd_customer_asset_daily")

delta_table.alias("target").merge(
    source_df.alias("source"),
    "target.stat_date = source.stat_date AND target.customer_id = source.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# 可以回溯到任意历史版本
df_yesterday = spark.read.format("delta") \
    .option("versionAsOf", 100) \
    .load("s3://lake/dwd_customer_asset_daily")
```

---

### 例子2：Schema 演进（当前 vs 湖仓）

#### 当前项目
```sql
-- 要加字段，必须手动改 DDL + 改 ETL + 重建表
ALTER TABLE dwd_customer_asset_daily 
ADD COLUMN risk_level VARCHAR(20) COMMENT '风险等级';

-- 然后要重新跑全量 ETL
-- 旧数据的 risk_level 全是 NULL
```

#### 湖仓一体（自动 Schema 演进）
```python
# Delta Lake 自动处理 Schema 变化
spark.read.parquet("s3://lake/ods_customer") \
    .withColumn("risk_level", lit("medium")) \
    .write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("s3://lake/dwd_customer")
# 新字段自动加入，旧数据自动填充默认值
```

---

### 例子3：Time Travel（当前 vs 湖仓）

#### 当前项目
```sql
-- 无法知道 3 天前的 customer_id=C001 的 AUM 是多少
-- 因为数据被覆盖了
SELECT total_aum FROM dws_customer_value_profile 
WHERE customer_id = 'C001' AND stat_date = '2026-06-12';
-- 可能已经不存在了
```

#### 湖仓一体
```python
# 查询 3 天前的历史数据
df_history = spark.read.format("delta") \
    .option("timestampAsOf", "2026-06-12") \
    .load("s3://lake/dws_customer_value_profile")

df_history.filter("customer_id = 'C001'").show()

# 或者按版本号查询
df_v50 = spark.read.format("delta") \
    .option("versionAsOf", 50) \
    .load("s3://lake/dws_customer_value_profile")
```

---

### 例子4：流批一体（当前 vs 湖仓）

#### 当前项目
```python
# 只能批处理：每天跑一次 ETL
# 实时数据需要单独写代码
# 无法做到"实时看到最新数据"
```

#### 湖仓一体（Flink + Delta Lake）
```python
# Flink 实时写入 Delta Lake
from pyflink.table import EnvironmentSettings, TableEnvironment

env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

# 实时消费 Kafka 交易数据
t_env.execute_sql("""
    INSERT INTO delta_sink
    SELECT 
        transaction_date,
        customer_id,
        SUM(amount) as total_amount
    FROM kafka_source
    GROUP BY transaction_date, customer_id
""")

# 同时可以用 Spark 批量读取做分析
# 同一张表，既支持实时写入，又支持批量查询
```

---

## 五、架构图对比

### 当前项目架构
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CSV 文件    │────▶│    MySQL     │────▶│  Streamlit  │
│  (本地磁盘)  │     │  (OLTP引擎)  │     │   (前端)    │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    │ ODS/DWD/  │
                    │ DWS/ADS   │
                    └───────────┘
```

### 湖仓一体架构
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Kafka   │  │  MySQL   │  │   API    │
│  (实时流) │  │  (业务库) │  │  (外部)  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     ▼             ▼             ▼
┌─────────────────────────────────────┐
│         湖仓存储层 (S3/HDFS)         │
│  ┌─────────┐ ┌─────────┐ ┌────────┐│
│  │  Raw    │ │ Curated │ │  Refined││
│  │ (Parquet)│ │ (Delta) │ │ (Delta)││
│  └─────────┘ └─────────┘ └────────┘│
└─────────────────────────────────────┘
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Spark  │  │  Flink  │  │  Trino  │
│  (批处理) │  │ (流处理) │  │ (即席查询)│
└────┬────┘  └────┬────┘  └────┬────┘
     │             │             │
     ▼             ▼             ▼
┌─────────────────────────────────────┐
│           应用层                      │
│  BI看板 │ 机器学习 │ 实时大屏 │ API  │
└─────────────────────────────────────┘
```

---

## 六、当前项目如何演进到湖仓

如果要升级，核心步骤：

1. **存储迁移**：MySQL → MinIO/S3 + Delta Lake
2. **格式转换**：MySQL 行存储 → Parquet 列式存储
3. **引擎升级**：纯 SQL → Spark/Flink 计算
4. **增量处理**：全量刷新 → MERGE 增量更新
5. **版本控制**：无 → Time Travel 历史回溯

### 结论

对于当前的学习项目，传统数仓架构已经足够。湖仓一体更适合**生产级大数据场景**（TB/PB 级数据量、实时需求、多团队协作）。

---

## 七、核心概念速查

| 概念 | 说明 |
|---|---|
| **Delta Lake** | 开源表格式，在数据湖上实现 ACID 事务、Time Travel、Schema 演进 |
| **Apache Iceberg** | 另一种开源表格式，支持隐藏分区、快照隔离 |
| **Apache Hudi** | 支持增量处理和近实时数据湖的表格式 |
| **Parquet** | 列式存储格式，压缩率高，分析查询快 |
| **ORC** | 另一种列式存储格式，Hive 生态常用 |
| **MERGE/UPSERT** | 增量更新操作，只更新变化的数据 |
| **Time Travel** | 时间旅行，查询历史版本的数据 |
| **Schema Evolution** | Schema 演进，自动处理表结构变化 |
| **流批一体** | 同一套代码同时处理实时流和批量数据 |
