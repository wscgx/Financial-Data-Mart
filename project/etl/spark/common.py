"""
ETL 公共工具函数
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def log_etl_start(table_name, target_date=None):
    """记录 ETL 开始"""
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"[ETL] {table_name} - date: {target_date}")
    print(f"{'='*60}")
    return target_date


def log_etl_end(table_name, count):
    """记录 ETL 结束"""
    print(f"\n[OK] {table_name}: {count:,} rows processed")
    print(f"{'='*60}\n")


def log_etl_error(table_name, error):
    """记录 ETL 错误"""
    print(f"\n[ERROR] {table_name}: {error}")
    print(f"{'='*60}\n")


def get_spark_config():
    """获取 Spark 配置"""
    from configs.spark_config import (
        MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY,
        MYSQL_URL, MYSQL_PROPERTIES, KAFKA_BOOTSTRAP_SERVERS
    )
    return {
        "minio_endpoint": MINIO_ENDPOINT,
        "minio_access_key": MINIO_ACCESS_KEY,
        "minio_secret_key": MINIO_SECRET_KEY,
        "mysql_url": MYSQL_URL,
        "mysql_properties": MYSQL_PROPERTIES,
        "kafka_bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    }
