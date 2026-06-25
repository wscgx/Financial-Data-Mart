"""
ETL: Delta Lake ODS → Delta Lake DWD
使用 PySpark SQL 实现清洗转换

用法:
    python etl_dwd_to_delta.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_delta_table, write_delta_table,
    ODS_PATH, DWD_PATH
)

DWD_ETL_SQL = {
    "dwd_customer_asset_daily": """
        SELECT
            t.transaction_date AS stat_date,
            t.customer_id,
            t.account_id,
            SUM(CASE WHEN t.transaction_type = 'holding' THEN t.amount ELSE 0 END) AS holding_market_value,
            SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
            SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount,
            'ods_transaction' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{ods_path}/ods_transaction` t
        WHERE t.transaction_date = '{target_date}'
        GROUP BY t.transaction_date, t.customer_id, t.account_id
    """,
    "dwd_customer_activity_daily": """
        SELECT
            t.transaction_date AS stat_date,
            t.customer_id,
            t.account_id,
            COUNT(*) AS transaction_count,
            SUM(CASE WHEN t.transaction_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_count,
            SUM(CASE WHEN t.transaction_type = 'redemption' THEN 1 ELSE 0 END) AS redemption_count,
            SUM(t.amount) AS total_amount,
            'ods_transaction' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{ods_path}/ods_transaction` t
        WHERE t.transaction_date = '{target_date}'
        GROUP BY t.transaction_date, t.customer_id, t.account_id
    """,
    "dwd_customer_risk_match": """
        SELECT
            h.as_of_date AS stat_date,
            h.customer_id,
            h.account_id,
            h.product_id,
            h.market_value,
            p.risk_level AS product_risk_level,
            ra.risk_tolerance AS customer_risk_tolerance,
            CASE
                WHEN p.risk_level = 'low' AND ra.risk_tolerance IN ('conservative', 'moderate') THEN '匹配'
                WHEN p.risk_level = 'medium' AND ra.risk_tolerance IN ('moderate', 'aggressive') THEN '匹配'
                WHEN p.risk_level = 'high' AND ra.risk_tolerance = 'aggressive' THEN '匹配'
                ELSE '不匹配'
            END AS risk_match_status,
            'ods_holding' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{ods_path}/ods_holding` h
        LEFT JOIN delta.`{ods_path}/ods_product` p ON h.product_id = p.product_id
        LEFT JOIN delta.`{ods_path}/ods_risk_assessment` ra ON h.customer_id = ra.customer_id
        WHERE h.is_current = 1
    """,
    "dwd_product_sales_daily": """
        SELECT
            t.transaction_date AS stat_date,
            t.product_id,
            p.product_name,
            p.product_type,
            p.risk_level,
            SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
            SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount,
            COUNT(*) AS transaction_count,
            'ods_transaction' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{ods_path}/ods_transaction` t
        LEFT JOIN delta.`{ods_path}/ods_product` p ON t.product_id = p.product_id
        WHERE t.transaction_date = '{target_date}'
        GROUP BY t.transaction_date, t.product_id, p.product_name, p.product_type, p.risk_level
    """,
}


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] Delta ODS → Delta DWD - date: {target_date}")
    print("=" * 60)

    for table_name, sql_template in DWD_ETL_SQL.items():
        print(f"\n  处理表: {table_name}")

        # 填充 SQL 模板
        sql = sql_template.format(ods_path=ODS_PATH, target_date=target_date)

        # 执行 SQL
        df = spark.sql(sql)
        count = df.count()

        # 写入 Delta Lake
        target_path = f"{DWD_PATH}/{table_name}"
        write_delta_table(df, target_path, mode="overwrite", partition_by="stat_date")

        print(f"    ✓ {count:,} 行 → {target_path}")

    print("\n" + "=" * 60)
    print(f"DWD 层构建完成! 共 {len(DWD_ETL_SQL)} 张表")


def main():
    parser = argparse.ArgumentParser(description="Delta ODS → Delta DWD ETL")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_DWD_to_Delta")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
