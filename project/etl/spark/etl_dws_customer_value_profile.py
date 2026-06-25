"""
ETL: DWD -> DWS (PySpark + Delta Lake)
dws_customer_value_profile 客户价值画像表

用法:
    python etl_dws_customer_value_profile.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_mysql_table, write_delta_table,
    DWD_PATH, DWS_PATH
)


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] dws_customer_value_profile - date: {target_date}")

    from pyspark.sql import functions as F

    # ── 1. 读取 DWD 层数据 ──────────────────────────────────
    dwd_asset = spark.read.format("delta").load(f"{DWD_PATH}/dwd_customer_asset_daily")
    ods_customer = read_mysql_table(spark, "ods_customer").filter("is_current = 1")

    # ── 2. 过滤目标日期 ─────────────────────────────────────
    daily_asset = dwd_asset.filter(F.col("stat_date") == target_date)

    # ── 3. 聚合客户价值指标 ─────────────────────────────────
    result = (
        daily_asset
        .groupBy("customer_id", "customer_name", "city")
        .agg(
            F.sum("holding_market_value").alias("total_holding_value"),
            F.sum("purchase_amount").alias("total_purchase"),
            F.sum("redemption_amount").alias("total_redemption"),
            F.sum("profit_loss").alias("total_profit_loss"),
            F.sum("net_asset_change").alias("total_net_asset_change"),
            F.count("*").alias("account_count"),
            F.avg("holding_market_value").alias("avg_holding_value"),
            F.max("holding_market_value").alias("max_holding_value"),
        )
        .withColumn("total_aum", F.col("total_holding_value"))
    )

    # ── 4. 计算客户等级 ─────────────────────────────────────
    quantiles = result.approxQuantile("total_aum", [0.25, 0.5, 0.75, 0.9], 0.01)
    q25, q50, q75, q90 = quantiles if len(quantiles) >= 4 else [0, 0, 0, 0]

    result = result.withColumn(
        "level_name",
        F.when(F.col("total_aum") >= q90, "超高净值客户")
        .when(F.col("total_aum") >= q75, "高净值客户")
        .when(F.col("total_aum") >= q50, "中端客户")
        .when(F.col("total_aum") >= q25, "潜力客户")
        .otherwise("普通客户")
    )

    # ── 5. 添加元数据字段 ───────────────────────────────────
    result = (
        result
        .withColumn("stat_date", F.lit(target_date))
        .withColumn("dm_src_info", F.lit("dwd_customer_asset_daily"))
        .withColumn("etl_load_time", F.current_timestamp())
        .select(
            "stat_date", "customer_id", "customer_name", "city",
            "total_aum", "total_holding_value", "total_purchase",
            "total_redemption", "total_profit_loss", "total_net_asset_change",
            "account_count", "avg_holding_value", "max_holding_value",
            "level_name", "dm_src_info", "etl_load_time",
        )
    )

    # ── 6. 写入 Delta Lake ──────────────────────────────────
    target_path = f"{DWS_PATH}/dws_customer_value_profile"
    write_delta_table(result, target_path, mode="overwrite", partition_by="stat_date")

    count = spark.read.format("delta").load(target_path).count()
    print(f"[ETL] dws_customer_value_profile 完成: {count} 行")

    return count


def main():
    parser = argparse.ArgumentParser(description="DWS - 客户价值画像 ETL")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_DWS_CustomerValueProfile")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
