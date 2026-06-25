"""
ETL: Delta Lake ADS → MySQL
将分析层结果回写 MySQL 供 Streamlit 读取

用法:
    python etl_ads_sync_mysql.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_delta_table, write_to_mysql,
    ADS_PATH
)

ADS_TABLES = [
    "ads_executive_dashboard",
    "ads_customer_churn_warning",
    "ads_customer_value_level_dist",
    "ads_customer_aum_ranking",
    "ads_risk_mismatch_alert",
    "ads_customer_net_asset_change",
    "ads_customer_aum_daily",
    "ads_branch_sales_ranking",
]


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] Delta ADS → MySQL - date: {target_date}")
    print("=" * 60)

    for table in ADS_TABLES:
        print(f"\n  同步表: {table}")

        # 从 Delta Lake 读取
        source_path = f"{ADS_PATH}/{table}"
        try:
            df = spark.read.format("delta").load(source_path)
            df = df.filter(f"stat_date = '{target_date}'")
            count = df.count()

            if count == 0:
                print(f"    ⚠ 无数据可同步 (stat_date={target_date})")
                continue

            # 写入 MySQL
            write_to_mysql(df, table, mode="overwrite")
            print(f"    ✓ {count:,} 行 → MySQL {table}")
        except Exception as e:
            print(f"    ✗ 同步失败: {e}")

    print("\n" + "=" * 60)
    print("ADS 层数据同步到 MySQL 完成!")


def main():
    parser = argparse.ArgumentParser(description="Delta ADS → MySQL Sync")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_ADS_Sync_MySQL")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
