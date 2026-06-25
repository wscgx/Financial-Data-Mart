"""
Delta Lake 性能优化脚本

功能：
    1. Z-Order 索引优化 - 加速查询
    2. 数据压缩 - 减少存储空间
    3. 清理旧版本 - 释放空间

用法：
    python optimize_delta_tables.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from configs.spark_config import get_spark_session, WAREHOUSE_PATH


DELTA_TABLES = [
    {"path": "ods/ods_customer", "z_order_cols": ["customer_id"]},
    {"path": "ods/ods_account", "z_order_cols": ["customer_id", "account_id"]},
    {"path": "ods/ods_product", "z_order_cols": ["product_id", "product_type"]},
    {"path": "ods/ods_transaction", "z_order_cols": ["customer_id", "transaction_date"]},
    {"path": "ods/ods_holding", "z_order_cols": ["customer_id", "product_id"]},
    {"path": "dwd/dwd_customer_asset_daily", "z_order_cols": ["customer_id", "stat_date"]},
    {"path": "dws/dws_customer_value_profile", "z_order_cols": ["customer_id"]},
    {"path": "ads/ads_executive_dashboard", "z_order_cols": ["stat_date"]},
    {"path": "ads/ads_customer_aum_daily", "z_order_cols": ["customer_id", "stat_date"]},
]


def optimize_tables():
    """执行 Delta Lake 表优化"""
    print("=" * 60)
    print("  Delta Lake 性能优化")
    print("=" * 60)

    spark = get_spark_session("Delta_Optimization")

    for table in DELTA_TABLES:
        table_path = f"{WAREHOUSE_PATH}/{table['path']}"
        z_order_cols = table['z_order_cols']

        print(f"\n[优化] {table['path']}")

        try:
            delta_table = spark.read.format("delta").load(table_path)

            print(f"  当前行数: {delta_table.count()}")

            from delta.tables import DeltaTable
            delta_obj = DeltaTable.forPath(spark, table_path)

            delta_obj.optimize().executeZOrderBy(*z_order_cols)
            print(f"  Z-Order 索引已创建: {', '.join(z_order_cols)}")

            delta_obj.vacuum(168)
            print(f"  旧版本已清理 (保留168小时)")

            print(f"  状态: 完成")

        except Exception as e:
            print(f"  状态: 跳过 - {str(e)[:60]}")

    spark.stop()

    print("\n" + "=" * 60)
    print("  优化完成")
    print("=" * 60)


if __name__ == "__main__":
    optimize_tables()
