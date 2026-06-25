"""
数据质量校验脚本 - 基于 Great Expectations 思路的轻量级实现

功能：
    对数仓各层表进行质量校验
    输出校验报告到 CSV

用法：
    python run_validation.py
"""
import os
import sys
import csv
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from configs.spark_config import get_spark_session, MYSQL_URL, MYSQL_PROPERTIES


VALIDATION_RULES = [
    {
        "name": "ods_customer_completeness",
        "desc": "ODS客户表完整性校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_count FROM ods_customer",
        "check_type": "completeness",
        "threshold": 0
    },
    {
        "name": "ods_customer_uniqueness",
        "desc": "ODS客户表唯一性校验",
        "sql": "SELECT COUNT(*) AS total, COUNT(DISTINCT customer_id) AS distinct_count FROM ods_customer",
        "check_type": "uniqueness",
        "threshold": 0
    },
    {
        "name": "ods_transaction_completeness",
        "desc": "ODS交易表完整性校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) AS null_count FROM ods_transaction",
        "check_type": "completeness",
        "threshold": 0
    },
    {
        "name": "dwd_asset_daily_completeness",
        "desc": "DWD客户资产日快照完整性校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN customer_id IS NULL OR stat_date IS NULL THEN 1 ELSE 0 END) AS null_count FROM dwd_customer_asset_daily",
        "check_type": "completeness",
        "threshold": 0
    },
    {
        "name": "dwd_asset_daily_consistency",
        "desc": "DWD客户资产日快照勾稽关系校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN holding_market_value < 0 THEN 1 ELSE 0 END) AS negative_count FROM dwd_customer_asset_daily",
        "check_type": "consistency",
        "threshold": 0
    },
    {
        "name": "dws_value_profile_completeness",
        "desc": "DWS客户价值画像完整性校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_count FROM dws_customer_value_profile",
        "check_type": "completeness",
        "threshold": 0
    },
    {
        "name": "ads_dashboard_completeness",
        "desc": "ADS高管驾驶舱完整性校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN stat_date IS NULL THEN 1 ELSE 0 END) AS null_count FROM ads_executive_dashboard",
        "check_type": "completeness",
        "threshold": 0
    },
    {
        "name": "ads_aum_daily_timeliness",
        "desc": "ADS客户AUM日汇总时效性校验",
        "sql": "SELECT COUNT(*) AS total, SUM(CASE WHEN stat_date < DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS stale_count FROM ads_customer_aum_daily",
        "check_type": "timeliness",
        "threshold": 0
    },
]


def run_validation():
    """执行数据质量校验"""
    print("=" * 60)
    print("  数据质量校验开始")
    print("=" * 60)

    results = []

    try:
        import pymysql
        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3307")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "123456"),
            database=os.getenv("MYSQL_DATABASE", "financial_dw"),
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        for rule in VALIDATION_RULES:
            print(f"\n[校验] {rule['desc']}")

            try:
                cursor.execute(rule['sql'])
                row = cursor.fetchone()
                columns = [desc[0] for desc in cursor.description]
                result = dict(zip(columns, row))

                total = result.get('total', 0)
                failed = 0
                for key, val in result.items():
                    if key != 'total' and val is not None:
                        failed = val
                        break

                status = "PASS" if failed <= rule['threshold'] else "FAIL"

                results.append({
                    "check_name": rule['name'],
                    "description": rule['desc'],
                    "check_type": rule['check_type'],
                    "total_records": total,
                    "failed_records": failed,
                    "threshold": rule['threshold'],
                    "status": status,
                    "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                print(f"  结果: {status} (总行数: {total}, 失败: {failed})")

            except Exception as e:
                results.append({
                    "check_name": rule['name'],
                    "description": rule['desc'],
                    "check_type": rule['check_type'],
                    "total_records": 0,
                    "failed_records": -1,
                    "threshold": rule['threshold'],
                    "status": "ERROR",
                    "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"  结果: ERROR - {str(e)[:50]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n数据库连接失败: {e}")
        print("请确保 MySQL 服务正在运行，并检查连接配置")

    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'quality_reports')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quality_report_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    if results:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        latest_link = os.path.join(output_dir, "quality_report_latest.csv")
        if os.path.exists(latest_link) or os.path.islink(latest_link):
            os.remove(latest_link)

        try:
            os.symlink(filepath, latest_link)
        except OSError:
            import shutil
            shutil.copy2(filepath, latest_link)

        print(f"\n校验报告已保存: {filepath}")

    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')

    print("\n" + "=" * 60)
    print(f"  校验完成: 通过 {pass_count}, 失败 {fail_count}, 错误 {error_count}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_validation()
