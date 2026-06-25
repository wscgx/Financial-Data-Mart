"""
Flink 流处理作业 - Kafka 实时聚合交易数据

用法 (PyFlink):
    python flink_realtime_agg.py

功能:
    从 Kafka 读取实时交易消息
    按产品类型 + 时间窗口聚合交易金额和笔数
    输出聚合结果到 Delta Lake (MinIO)
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_flink_sql_job():
    """运行 Flink SQL 实时聚合作业"""
    try:
        from pyflink.table import EnvironmentSettings, TableEnvironment
        from pyflink.table.expressions import col, lit
    except ImportError:
        print("请先安装 PyFlink: pip install apache-flink")
        print("或使用 Docker 中的 Flink 集群")
        return

    # ── 1. 创建 Flink Table Environment ─────────────────────
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # 配置 Kafka 连接器
    t_env.execute_sql("""
        CREATE TABLE kafka_transactions (
            transaction_id STRING,
            account_id STRING,
            customer_id STRING,
            product_id STRING,
            product_name STRING,
            product_type STRING,
            risk_level STRING,
            transaction_type STRING,
            amount DOUBLE,
            price DOUBLE,
            quantity DOUBLE,
            fee DOUBLE,
            branch STRING,
            transaction_time STRING,
            status STRING,
            proctime AS PROCTIME()
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'financial_transactions',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'flink_financial_agg',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # ── 2. 创建 Delta Lake 输出表 ────────────────────────────
    t_env.execute_sql("""
        CREATE TABLE delta_realtime_agg (
            product_type STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            total_amount DOUBLE,
            transaction_count BIGINT,
            avg_amount DOUBLE,
            PRIMARY KEY (product_type, window_start) NOT ENFORCED
        ) WITH (
            'connector' = 'filesystem',
            'path' = 's3a://financial-data-lake/dws/dws_realtime_transaction_agg',
            'format' = 'json',
            'sink.partition-commit.trigger' = 'process-time',
            'sink.partition-commit.delay' = '1 min'
        )
    """)

    # ── 3. 创建 MySQL 输出表 (用于实时同步) ──────────────────
    t_env.execute_sql("""
        CREATE TABLE mysql_realtime_agg (
            product_type STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            total_amount DOUBLE,
            transaction_count BIGINT,
            avg_amount DOUBLE,
            PRIMARY KEY (product_type, window_start) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:mysql://mysql:3306/financial_dw',
            'table-name' = 'dws_realtime_transaction_agg',
            'username' = 'root',
            'password' = '123456'
        )
    """)

    # ── 4. 执行窗口聚合 SQL 并写入 Delta Lake ────────────────
    t_env.execute_sql("""
        INSERT INTO delta_realtime_agg
        SELECT
            product_type,
            TUMBLE_START(proctime, INTERVAL '10' SECOND) AS window_start,
            TUMBLE_END(proctime, INTERVAL '10' SECOND) AS window_end,
            SUM(amount) AS total_amount,
            COUNT(*) AS transaction_count,
            AVG(amount) AS avg_amount
        FROM kafka_transactions
        WHERE transaction_type = 'purchase'
        GROUP BY
            product_type,
            TUMBLE(proctime, INTERVAL '10' SECOND)
    """)

    # ── 5. 执行窗口聚合 SQL 并写入 MySQL ────────────────────
    t_env.execute_sql("""
        INSERT INTO mysql_realtime_agg
        SELECT
            product_type,
            TUMBLE_START(proctime, INTERVAL '10' SECOND) AS window_start,
            TUMBLE_END(proctime, INTERVAL '10' SECOND) AS window_end,
            SUM(amount) AS total_amount,
            COUNT(*) AS transaction_count,
            AVG(amount) AS avg_amount
        FROM kafka_transactions
        WHERE transaction_type = 'purchase'
        GROUP BY
            product_type,
            TUMBLE(proctime, INTERVAL '10' SECOND)
    """)

    print("Flink 实时聚合作业已启动!")
    print("输出目标: Delta Lake + MySQL")
    print("按 Ctrl+C 停止...")


def run_pyspark_streaming():
    """
    PySpark Structured Streaming 替代方案
    如果不想用 Flink，可以用 Spark Structured Streaming
    """
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
    except ImportError:
        print("请先安装 pyspark: pip install pyspark")
        return

    from configs.spark_config import (
        get_spark_session, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC,
        WAREHOUSE_PATH, CHECKPOINTS_PATH, MYSQL_URL, MYSQL_PROPERTIES
    )

    spark = get_spark_session("Financial_Realtime_Aggregation")

    # 从 Kafka 读取流
    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    # 解析 JSON
    schema = """
        transaction_id STRING,
        account_id STRING,
        customer_id STRING,
        product_id STRING,
        product_name STRING,
        product_type STRING,
        risk_level STRING,
        transaction_type STRING,
        amount DOUBLE,
        price DOUBLE,
        quantity DOUBLE,
        fee DOUBLE,
        branch STRING,
        transaction_time STRING,
        status STRING
    """

    parsed_stream = (
        raw_stream
        .selectExpr("CAST(value AS STRING) as json_str")
        .select(F.from_json(F.col("json_str"), schema).alias("data"))
        .select("data.*")
    )

    # 窗口聚合: 按产品类型 + 10秒窗口
    agg_stream = (
        parsed_stream
        .filter(F.col("transaction_type") == "purchase")
        .withWatermark("transaction_time", "30 seconds")
        .groupBy(
            F.col("product_type"),
            F.window(F.col("transaction_time"), "10 seconds")
        )
        .agg(
            F.sum("amount").alias("total_amount"),
            F.count("*").alias("transaction_count"),
            F.avg("amount").alias("avg_amount"),
            F.max("amount").alias("max_amount"),
        )
        .select(
            "product_type",
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "total_amount",
            "transaction_count",
            "avg_amount",
            "max_amount",
        )
    )

    # 输出到 Delta Lake
    delta_query = (
        agg_stream.writeStream
        .outputMode("update")
        .format("delta")
        .option("checkpointLocation", f"{CHECKPOINTS_PATH}/realtime_agg")
        .start(f"{WAREHOUSE_PATH}/dws_realtime_transaction_agg")
    )

    # 输出到 MySQL
    mysql_query = (
        agg_stream.writeStream
        .outputMode("update")
        .format("jdbc")
        .option("url", MYSQL_URL)
        .option("dbtable", "dws_realtime_transaction_agg")
        .options(**MYSQL_PROPERTIES)
        .option("checkpointLocation", f"{CHECKPOINTS_PATH}/realtime_agg_mysql")
        .start()
    )

    print("Spark Streaming 实时聚合作业已启动!")
    print("输出目标: Delta Lake + MySQL")
    print("按 Ctrl+C 停止...")

    delta_query.awaitTermination()
    mysql_query.awaitTermination()


def main():
    print("=" * 60)
    print("  金融交易实时聚合 - 流处理作业")
    print("=" * 60)
    print()
    print("  选择运行模式:")
    print("  1. Flink SQL (推荐，需要 Flink 集群)")
    print("  2. PySpark Structured Streaming (轻量)")
    print()

    choice = input("请选择 (1/2): ").strip()

    if choice == "1":
        run_flink_sql_job()
    elif choice == "2":
        run_pyspark_streaming()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
