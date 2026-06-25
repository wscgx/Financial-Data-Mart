"""
Delta Lake 交互查询工具
用法：
    python query_delta.py                          # 交互模式
    python query_delta.py "SELECT * FROM delta..."  # 直接执行SQL
    python query_delta.py --list                   # 列出所有表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from configs.spark_config import (
    get_spark_session, read_delta_table,
    ODS_PATH, DWD_PATH, DWS_PATH, ADS_PATH
)


def list_tables(spark):
    """列出 Delta Lake 中所有表"""
    tables = {
        "ODS": [
            "ods_customer", "ods_account", "ods_product",
            "ods_transaction", "ods_holding", "ods_risk_assessment"
        ],
        "DWD": [
            "dwd_customer_asset_daily", "dwd_customer_activity_daily",
            "dwd_customer_risk_match", "dwd_product_sales_daily"
        ],
        "DWS": [
            "dws_customer_value_profile", "dws_customer_behavior_profile",
            "dws_risk_compliance_summary", "dws_product_performance",
            "dws_platform_daily_summary"
        ],
        "ADS": [
            "ads_executive_dashboard", "ads_customer_churn_warning",
            "ads_customer_value_level_dist", "ads_customer_aum_ranking",
            "ads_risk_mismatch_alert", "ads_customer_net_asset_change",
            "ads_customer_aum_daily", "ads_branch_sales_ranking"
        ]
    }

    print("\n" + "=" * 60)
    print("Delta Lake 表清单")
    print("=" * 60)

    for layer, table_list in tables.items():
        print(f"\n【{layer}层】")
        for table in table_list:
            print(f"  - {table}")
    print()


def get_table_path(table_name):
    """根据表名获取 Delta Lake 路径"""
    layer = table_name.split("_")[0].upper()
    paths = {"ODS": ODS_PATH, "DWD": DWD_PATH, "DWS": DWS_PATH, "ADS": ADS_PATH}
    return f"{paths[layer]}/{table_name}"


def run_query(spark, sql):
    """执行 Spark SQL 查询"""
    print(f"\n执行查询: {sql[:100]}...")
    df = spark.sql(sql)
    df.show(50, truncate=False)
    return df


def interactive_mode(spark):
    """交互式查询模式"""
    print("\n" + "=" * 60)
    print("Delta Lake 交互查询模式")
    print("输入 SQL 查询，输入 'quit' 退出，输入 'list' 查看表清单")
    print("=" * 60)

    while True:
        try:
            sql = input("\nSQL> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出查询")
            break

        if not sql:
            continue
        if sql.lower() in ('quit', 'exit', 'q'):
            print("退出查询")
            break
        if sql.lower() == 'list':
            list_tables(spark)
            continue

        try:
            run_query(spark, sql)
        except Exception as e:
            print(f"查询错误: {e}")


if __name__ == "__main__":
    spark = get_spark_session("DeltaQuery")

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--list':
            list_tables(spark)
        else:
            run_query(spark, arg)
    else:
        interactive_mode(spark)

    spark.stop()
