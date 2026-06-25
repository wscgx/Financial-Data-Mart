"""
ETL: Delta Lake DWS/DWD → Delta Lake ADS
应用层数据加工

用法:
    python etl_ads_to_delta.py [--date 2026-06-23]
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.spark_config import (
    get_spark_session, read_delta_table, write_delta_table,
    DWD_PATH, DWS_PATH, ADS_PATH
)

ADS_ETL_SQL = {
    "ads_executive_dashboard": """
        SELECT
            stat_date,
            total_aum,
            total_purchase,
            total_redemption,
            active_customers,
            active_accounts,
            total_aum - LAG(total_aum, 1) OVER (ORDER BY stat_date) AS aum_change,
            'dws_platform_daily_summary' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dws_path}/dws_platform_daily_summary`
        WHERE stat_date = '{target_date}'
    """,
    "ads_customer_churn_warning": """
        SELECT
            stat_date,
            customer_id,
            customer_name,
            total_transactions,
            total_amount,
            CASE
                WHEN total_transactions < 3 THEN '低活跃'
                WHEN total_amount < 10000 THEN '低金额'
                ELSE '正常'
            END AS churn_risk_level,
            'dws_customer_behavior_profile' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dws_path}/dws_customer_behavior_profile`
        WHERE stat_date = '{target_date}'
    """,
    "ads_customer_value_level_dist": """
        SELECT
            stat_date,
            level_name,
            COUNT(*) AS customer_count,
            SUM(total_aum) AS total_aum,
            AVG(total_aum) AS avg_aum,
            'dws_customer_value_profile' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dws_path}/dws_customer_value_profile`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date, level_name
    """,
    "ads_customer_aum_ranking": """
        SELECT
            stat_date,
            customer_id,
            customer_name,
            city,
            total_aum,
            level_name,
            RANK() OVER (PARTITION BY stat_date ORDER BY total_aum DESC) AS aum_rank,
            'dws_customer_value_profile' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dws_path}/dws_customer_value_profile`
        WHERE stat_date = '{target_date}'
    """,
    "ads_risk_mismatch_alert": """
        SELECT
            stat_date,
            customer_id,
            product_id,
            market_value,
            product_risk_level,
            customer_risk_tolerance,
            risk_match_status,
            CASE
                WHEN risk_match_status = '不匹配' AND market_value > 100000 THEN '高风险'
                WHEN risk_match_status = '不匹配' THEN '中风险'
                ELSE '低风险'
            END AS alert_level,
            'dwd_customer_risk_match' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_risk_match`
        WHERE stat_date = '{target_date}'
    """,
    "ads_customer_net_asset_change": """
        SELECT
            stat_date,
            customer_id,
            customer_name,
            city,
            SUM(purchase_amount) AS total_purchase,
            SUM(redemption_amount) AS total_redemption,
            SUM(profit_loss) AS total_profit_loss,
            SUM(net_asset_change) AS total_net_asset_change,
            'dwd_customer_asset_daily' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_asset_daily`
        WHERE stat_date = '{target_date}'
        GROUP BY stat_date, customer_id, customer_name, city
    """,
    "ads_customer_aum_daily": """
        SELECT
            stat_date,
            customer_id,
            customer_name,
            city,
            holding_market_value AS total_aum,
            purchase_amount,
            redemption_amount,
            profit_loss,
            net_asset_change,
            'dwd_customer_asset_daily' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{dwd_path}/dwd_customer_asset_daily`
        WHERE stat_date = '{target_date}'
    """,
    "ads_branch_sales_ranking": """
        SELECT
            transaction_date AS stat_date,
            branch,
            SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END) AS total_purchase,
            SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END) AS total_redemption,
            COUNT(*) AS transaction_count,
            RANK() OVER (PARTITION BY transaction_date ORDER BY SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END) DESC) AS branch_rank,
            'ods_transaction' AS dm_src_info,
            CURRENT_TIMESTAMP() AS etl_load_time
        FROM delta.`{ods_path}/ods_transaction`
        WHERE transaction_date = '{target_date}'
        GROUP BY transaction_date, branch
    """,
}


def run(spark, target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[ETL] Delta DWS/DWD → Delta ADS - date: {target_date}")
    print("=" * 60)

    for table_name, sql_template in ADS_ETL_SQL.items():
        print(f"\n  处理表: {table_name}")

        # 填充 SQL 模板
        sql = sql_template.format(
            dwd_path=DWD_PATH,
            dws_path=DWS_PATH,
            ods_path=f"s3a://financial-data-lake/ods",
            target_date=target_date
        )

        # 执行 SQL
        df = spark.sql(sql)
        count = df.count()

        # 写入 Delta Lake
        target_path = f"{ADS_PATH}/{table_name}"
        write_delta_table(df, target_path, mode="overwrite", partition_by="stat_date")

        print(f"    ✓ {count:,} 行 → {target_path}")

    print("\n" + "=" * 60)
    print(f"ADS 层构建完成! 共 {len(ADS_ETL_SQL)} 张表")


def main():
    parser = argparse.ArgumentParser(description="Delta DWS/DWD → Delta ADS ETL")
    parser.add_argument("--date", default=None, help="目标日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    spark = get_spark_session("ETL_ADS_to_Delta")
    try:
        run(spark, target_date=args.date)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
