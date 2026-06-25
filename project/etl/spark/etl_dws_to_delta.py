"""
ETL: Delta Lake DWD → Delta Lake DWS
汇总层数据加工

用法:
    python etl_dws_to_delta.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_delta_table, write_delta_table,
    DWD_PATH, DWS_PATH
)

DWS_ETL_SQL = {
    "dws_customer_value_profile": """
        SELECT
            stat_date,
            customer_id,
            customer_name,
            city,
            SUM(holding_market_value) AS total_aum,
            SUM(purchase_amount) AS total_purchase,
            SUM(redemption_amount) AS total_redemption,
            SUM(profit_loss) AS total_profit_loss,
            SUM(net_asset_change) AS total_net_asset_change,
            COUNT(*) AS account_count,
            AVG(holding_market_value) AS avg_holding_value,
            MAX(holding_market_value) AS max_holding_value,
            CASE
                WHEN SUM(holding_market_value) >= 1000000 THEN '超高净值客户'
                WHEN SUM(holding_market_value) >= 500000 THEN '高净值客户'
                WHEN SUM(holding_market_value) >= 100000 THEN '中端客户'
                WHEN SUM(holding_market_value) >= 10000 THEN '潜力客户'
                ELSE '普通客户'
            END AS level_name,
            'dwd_customer_asset_daily' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_asset_daily`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date, customer_id, customer_name, city
    """,
    "dws_customer_behavior_profile": """
        SELECT
            stat_date,
            customer_id,
            customer_name,
            SUM(transaction_count) AS total_transactions,
            SUM(purchase_count) AS total_purchases,
            SUM(redemption_count) AS total_redemptions,
            SUM(total_amount) AS total_amount,
            AVG(total_amount) AS avg_transaction_amount,
            COUNT(DISTINCT account_id) AS active_accounts,
            'dwd_customer_activity_daily' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_activity_daily`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date, customer_id, customer_name
    """,
    "dws_risk_compliance_summary": """
        SELECT
            stat_date,
            customer_id,
            SUM(CASE WHEN risk_match_status = '匹配' THEN 1 ELSE 0 END) AS matched_count,
            SUM(CASE WHEN risk_match_status = '不匹配' THEN 1 ELSE 0 END) AS mismatched_count,
            COUNT(*) AS total_holdings,
            ROUND(SUM(CASE WHEN risk_match_status = '匹配' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS match_rate,
            'dwd_customer_risk_match' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_risk_match`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date, customer_id
    """,
    "dws_product_performance": """
        SELECT
            stat_date,
            product_id,
            product_name,
            product_type,
            risk_level,
            SUM(purchase_amount) AS total_purchase,
            SUM(redemption_amount) AS total_redemption,
            SUM(purchase_amount) - SUM(redemption_amount) AS net_flow,
            SUM(transaction_count) AS total_transactions,
            AVG(purchase_amount) AS avg_purchase_amount,
            'dwd_product_sales_daily' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_product_sales_daily`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date, product_id, product_name, product_type, risk_level
    """,
    "dws_platform_daily_summary": """
        SELECT
            stat_date,
            SUM(holding_market_value) AS total_aum,
            SUM(purchase_amount) AS total_purchase,
            SUM(redemption_amount) AS total_redemption,
            COUNT(DISTINCT customer_id) AS active_customers,
            COUNT(DISTINCT account_id) AS active_accounts,
            'dwd_customer_asset_daily' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_asset_daily`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date
    """,
}


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] Delta DWD → Delta DWS - date: {target_date}")
    print("=" * 60)

    for table_name, sql_template in DWS_ETL_SQL.items():
        print(f"\n  处理表: {table_name}")

        # 填充 SQL 模板
        sql = sql_template.format(dwd_path=DWD_PATH, target_date=target_date)

        # 执行 SQL
        df = spark.sql(sql)
        count = df.count()

        # 写入 Delta Lake
        target_path = f"{DWS_PATH}/{table_name}"
        write_delta_table(df, target_path, mode="overwrite", partition_by="stat_date")

        print(f"    ✓ {count:,} 行 → {target_path}")

    print("\n" + "=" * 60)
    print(f"DWS 层构建完成! 共 {len(DWS_ETL_SQL)} 张表")


def main():
    parser = argparse.ArgumentParser(description="Delta DWD → Delta DWS ETL")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_DWS_to_Delta")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
