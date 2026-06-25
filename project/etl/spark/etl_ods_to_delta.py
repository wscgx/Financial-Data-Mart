"""
ETL: MySQL ODS → Delta Lake (MinIO)
全量同步 ODS 层数据到数据湖

用法:
    python etl_ods_to_delta.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_mysql_table, write_delta_table,
    ODS_PATH
)

ODS_TABLES = [
    "ods_customer",
    "ods_account",
    "ods_product",
    "ods_transaction",
    "ods_holding",
    "ods_risk_assessment",
]


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] ODS to Delta Lake - date: {target_date}")
    print("=" * 60)

    for table in ODS_TABLES:
        print(f"\n  同步表: {table}")

        # 从 MySQL 读取
        df = read_mysql_table(spark, table)
        count = df.count()

        # 写入 Delta Lake
        target_path = f"{ODS_PATH}/{table}"
        write_delta_table(df, target_path, mode="overwrite", partition_by=None)

        print(f"    ✓ {count:,} 行 → {target_path}")

    print("\n" + "=" * 60)
    print(f"ODS 层全量同步完成! 共 {len(ODS_TABLES)} 张表")


def main():
    parser = argparse.ArgumentParser(description="ODS to Delta Lake ETL")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_ODS_to_Delta")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
