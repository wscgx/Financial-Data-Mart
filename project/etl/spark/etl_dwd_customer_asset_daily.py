"""
ETL: ODS -> DWD (PySpark + Delta Lake)
dwd_customer_asset_daily 客户资产日快照表

用法:
    python etl_dwd_customer_asset_daily.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_mysql_table, write_delta_table, merge_delta_table,
    ODS_PATH, DWD_PATH
)


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] dwd_customer_asset_daily - date: {target_date}")

    # ── 1. 读取 ODS 层数据 ──────────────────────────────────
    ods_holding = read_mysql_table(spark, "ods_holding")
    ods_account = read_mysql_table(spark, "ods_account")
    ods_customer = read_mysql_table(spark, "ods_customer")
    ods_transaction = read_mysql_table(spark, "ods_transaction")

    # ── 2. 过滤当前版本 ─────────────────────────────────────
    holding = ods_holding.filter("is_current = 1")
    account = ods_account.filter("is_current = 1")
    customer = ods_customer.filter("is_current = 1")

    # ── 3. 聚合交易数据 ─────────────────────────────────────
    from pyspark.sql import functions as F

    transaction_agg = (
        ods_transaction
        .filter(F.col("transaction_type").isin("purchase", "redemption"))
        .groupBy("account_id", "transaction_date")
        .agg(
            F.sum(F.when(F.col("transaction_type") == "purchase", F.col("amount")).otherwise(0))
                .alias("purchase_amount"),
            F.sum(F.when(F.col("transaction_type") == "redemption", F.col("amount")).otherwise(0))
                .alias("redemption_amount"),
        )
    )

    # ── 4. JOIN 构建 DWD 表 ─────────────────────────────────
    result = (
        holding
        .join(account, holding.account_id == account.account_id, "left")
        .join(customer, account.customer_id == customer.customer_id, "left")
        .join(
            transaction_agg,
            (account.account_id == transaction_agg.account_id) &
            (holding.as_of_date == transaction_agg.transaction_date),
            "left",
        )
        .select(
            holding.as_of_date.alias("stat_date"),
            account.customer_id,
            holding.account_id,
            F.concat(customer.last_name, customer.first_name).alias("customer_name"),
            customer.city,
            account.branch,
            F.coalesce(holding.market_value, F.lit(0)).alias("holding_market_value"),
            F.coalesce(transaction_agg.purchase_amount, F.lit(0)).alias("purchase_amount"),
            F.coalesce(transaction_agg.redemption_amount, F.lit(0)).alias("redemption_amount"),
            F.coalesce(holding.profit_loss, F.lit(0)).alias("profit_loss"),
            (
                F.coalesce(transaction_agg.purchase_amount, F.lit(0))
                - F.coalesce(transaction_agg.redemption_amount, F.lit(0))
                + F.coalesce(holding.profit_loss, F.lit(0))
            ).alias("net_asset_change"),
            F.lit("ods_holding").alias("dm_src_info"),
            F.current_timestamp().alias("etl_load_time"),
        )
    )

    # ── 5. 写入 Delta Lake ──────────────────────────────────
    target_path = f"{DWD_PATH}/dwd_customer_asset_daily"
    count_before = spark.read.format("delta").load(target_path).count() if os.path.exists(target_path.replace("s3a://", "/tmp/")) else 0

    write_delta_table(result, target_path, mode="overwrite", partition_by="stat_date")

    count_after = spark.read.format("delta").load(target_path).count()
    print(f"[ETL] dwd_customer_asset_daily 完成: {count_after} 行")

    return count_after


def main():
    parser = argparse.ArgumentParser(description="DWD - 客户资产日快照 ETL")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_DWD_CustomerAssetDaily")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
