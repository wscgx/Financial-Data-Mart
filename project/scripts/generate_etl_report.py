import pymysql
import csv
import os
from datetime import datetime

MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASS = '123456'
MYSQL_DB = 'financial_dw'

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
REPORT_DIR = os.path.join(BASE_DIR, 'data', 'quality_reports')
os.makedirs(REPORT_DIR, exist_ok=True)

conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                       password=MYSQL_PASS, database=MYSQL_DB, charset='utf8mb4')
cursor = conn.cursor()

now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 70)
print("  金融数据仓库 ETL 执行汇总报告")
print(f"  生成时间: {now_str}")
print("=" * 70)

total_rows = 0
total_tables = 0
report_rows = []

for tier in ['ods', 'dwd', 'dws', 'ads']:
    cursor.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema=%s AND table_name LIKE %s ORDER BY table_name",
        (MYSQL_DB, f'{tier}_%')
    )
    tables = cursor.fetchall()
    tier_count = len(tables)
    tier_rows = 0
    total_tables += tier_count

    print(f"\n[{tier.upper()} 层] {tier_count} 张表")
    for (tname,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{tname}`")
        cnt = cursor.fetchone()[0]
        tier_rows += cnt
        total_rows += cnt
        print(f"  {tname:<45s} {cnt:>10,} 行")
        report_rows.append({'tier': tier, 'table_name': tname, 'row_count': cnt})

    print(f"  {'小计':<45s} {tier_rows:>10,} 行")

# Data freshness
cursor.execute("SELECT MAX(etl_load_time) FROM dwd_customer_asset_daily")
r = cursor.fetchone()
freshness = r[0].strftime('%Y-%m-%d %H:%M:%S') if r and r[0] else 'N/A'

# Quality summary
q_file = os.path.join(REPORT_DIR, 'quality_report_latest.csv')
pass_count = fail_count = error_count = 0
if os.path.exists(q_file):
    with open(q_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = row.get('status', '')
            if s == 'PASS':
                pass_count += 1
            elif s == 'FAIL':
                fail_count += 1
            elif s == 'ERROR':
                error_count += 1

print(f"\n{'=' * 70}")
print(f"  总计: {total_tables} 张表, {total_rows:,} 行数据")
print(f"  数据新鲜度: {freshness}")
print(f"  质量校验: {pass_count} 通过 / {fail_count} 失败 / {error_count} 错误")
print(f"{'=' * 70}")

# Save CSV
csv_path = os.path.join(REPORT_DIR, f'etl_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['tier', 'table_name', 'row_count'])
    writer.writeheader()
    writer.writerows(report_rows)
print(f"\n  报告已保存: {csv_path}")

conn.close()
