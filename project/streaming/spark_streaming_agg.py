"""
Spark Structured Streaming - Kafka 实时聚合 (Flink 替代方案)

用法:
    python spark_streaming_agg.py

功能:
    从 Kafka 读取实时交易消息
    按产品类型 + 时间窗口聚合
    输出到 Delta Lake (MinIO) + MySQL
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def main():
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

    print("=" * 60)
    print("  Spark Structured Streaming - 实时交易聚合")
    print("=" * 60)

    # ── 1. 创建 SparkSession ────────────────────────────────
    spark = get_spark_session("Financial_Realtime_Aggregation")
    spark.sparkContext.setLogLevel("WARN")

    # ── 2. 从 Kafka 读取流 ─────────────────────────────────
    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    # ── 3. 解析 JSON 消息 ──────────────────────────────────
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

    # ── 4. 窗口聚合: 按产品类型 + 10秒窗口 ────────────────
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

    # ── 5. 输出到 Delta Lake ────────────────────────────────
    delta_query = (
        agg_stream.writeStream
        .outputMode("update")
        .format("delta")
        .option("checkpointLocation", f"{CHECKPOINTS_PATH}/realtime_agg")
        .start(f"{WAREHOUSE_PATH}/dws_realtime_transaction_agg")
    )

    # ── 6. 输出到 MySQL ─────────────────────────────────────
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
    print()

    delta_query.awaitTermination()
    mysql_query.awaitTermination()


if __name__ == "__main__":
    main()
