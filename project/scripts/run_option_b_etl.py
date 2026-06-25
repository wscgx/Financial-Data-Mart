import pymysql
import os
import datetime

MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASS = '123456'
MYSQL_DB = 'financial_dw'

SQL_DIR = os.path.join(os.path.dirname(__file__), '..', 'sql')
ETL_DIR = os.path.join(os.path.dirname(__file__), '..', 'etl')

def read_sql_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_file(cursor, filepath):
    sql = read_sql_file(filepath)
    lines = [line for line in sql.split('\n') if not line.strip().startswith('--')]
    clean_sql = '\n'.join(lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    for stmt in statements:
        cursor.execute(stmt)

def main():
    conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB, charset='utf8mb4')
    cursor = conn.cursor()

    print("=" * 60)
    print("选项B: 产品销售与业绩分析 - ETL 执行")
    print("=" * 60)

    print("\n[1/6] 创建 DWD 层表: dwd_product_sales_daily")
    execute_sql_file(cursor, os.path.join(SQL_DIR, 'dwd', 'dwd_product_sales_daily.sql'))
    conn.commit()
    print("  OK")

    print("\n[2/6] 创建 DWS 层表: dws_product_performance")
    execute_sql_file(cursor, os.path.join(SQL_DIR, 'dws', 'dws_product_performance.sql'))
    conn.commit()
    print("  OK")

    print("\n[3/6] 创建 ADS 层表: ads_branch_sales_ranking")
    execute_sql_file(cursor, os.path.join(SQL_DIR, 'ads', 'ads_branch_sales_ranking.sql'))
    conn.commit()
    print("  OK")

    print("\n[4/6] 执行 ODS -> DWD ETL: dwd_product_sales_daily")
    etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dwd_product_sales_daily.sql'))
    cursor.execute(etl_sql)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM dwd_product_sales_daily")
    count = cursor.fetchone()[0]
    print(f"  OK - 插入 {count} 条记录")

    print("\n[5/6] 执行 DWD -> DWS ETL: dws_product_performance")
    etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dws_product_performance.sql'))
    cursor.execute(etl_sql)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM dws_product_performance")
    count = cursor.fetchone()[0]
    print(f"  OK - 插入 {count} 条记录")

    print("\n[6/6] 执行 DWD+ODS -> ADS ETL: ads_branch_sales_ranking")
    etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_branch_sales_ranking.sql'))
    cursor.execute(etl_sql)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM ads_branch_sales_ranking")
    count = cursor.fetchone()[0]
    print(f"  OK - 插入 {count} 条记录")

    print("\n" + "=" * 60)
    print("数据验证")
    print("=" * 60)

    cursor.execute("""
        SELECT stat_date, product_id, product_name, purchase_amount, redemption_amount, net_purchase_amount
        FROM dwd_product_sales_daily
        ORDER BY stat_date DESC
        LIMIT 5
    """)
    print("\nDWD 层样例数据 (最近5条):")
    print(f"{'日期':<12} {'产品ID':<12} {'产品名称':<25} {'申购金额':>12} {'赎回金额':>12} {'净申购':>12}")
    print("-" * 90)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<12} {row[2]:<25} {row[3]:>12,.2f} {row[4]:>12,.2f} {row[5]:>12,.2f}")

    cursor.execute("""
        SELECT stat_date, product_id, product_name, total_sales_amount, total_customer_count, avg_daily_sales
        FROM dws_product_performance
        ORDER BY stat_date DESC
        LIMIT 5
    """)
    print("\nDWS 层样例数据 (最近5条):")
    print(f"{'日期':<12} {'产品ID':<12} {'产品名称':<25} {'累计销售':>12} {'客户数':>8} {'日均销售':>12}")
    print("-" * 90)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<12} {row[2]:<25} {row[3]:>12,.2f} {row[4]:>8} {row[5]:>12,.2f}")

    cursor.execute("""
        SELECT stat_date, branch, total_sales_amount, sales_ranking, sales_share
        FROM ads_branch_sales_ranking
        ORDER BY stat_date DESC, sales_ranking
        LIMIT 10
    """)
    print("\nADS 层样例数据 - 网点销售排名 (最近10条):")
    print(f"{'日期':<12} {'网点':<20} {'销售总额':>12} {'排名':>6} {'占比':>8}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<20} {row[2]:>12,.2f} {row[3]:>6} {row[4]:>8.2%}")

    conn.close()
    print("\n" + "=" * 60)
    print("ETL 执行完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
