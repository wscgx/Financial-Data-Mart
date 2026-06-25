import pymysql
import os
import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Config
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

def execute_ddl(cursor, filepath):
    """Execute DDL file (CREATE TABLE statements)"""
    sql = read_sql_file(filepath)
    # Remove comment lines
    lines = [line for line in sql.split('\n') if not line.strip().startswith('--')]
    clean_sql = '\n'.join(lines)
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    
    # Extract table name from CREATE TABLE statement
    table_name = None
    for stmt in statements:
        if 'CREATE TABLE' in stmt.upper():
            import re
            match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', stmt, re.IGNORECASE)
            if match:
                table_name = match.group(1)
            break
    
    # Drop table first to ensure comments are applied
    if table_name:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            # Ignore index already exists errors
            if 'Duplicate key' not in str(e) and '1061' not in str(e):
                raise

def execute_etl(cursor, filepath):
    """Execute ETL SQL file and return affected row count"""
    sql = read_sql_file(filepath)
    # Remove comment lines
    lines = [line for line in sql.split('\n') if not line.strip().startswith('--')]
    clean_sql = '\n'.join(lines)
    cursor.execute(clean_sql)
    return cursor.rowcount

def verify_comments(cursor, table_name):
    """Verify table and column comments in MySQL"""
    # Check table comment
    cursor.execute("""
        SELECT TABLE_COMMENT 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """, (MYSQL_DB, table_name))
    table_comment = cursor.fetchone()
    
    if table_comment and table_comment[0]:
        print(f"  表注释: {table_comment[0]}")
    else:
        print(f"  表注释: 缺失!")
    
    # Check column comments
    cursor.execute("""
        SELECT COLUMN_NAME, COLUMN_COMMENT 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """, (MYSQL_DB, table_name))
    
    missing_cols = []
    for row in cursor.fetchall():
        if not row[1]:
            missing_cols.append(row[0])
    
    if missing_cols:
        print(f"  字段注释缺失: {', '.join(missing_cols)}")
    else:
        print(f"  字段注释: 全部完整")

def main():
    try:
        print("=" * 60)
        print("选项B: 产品销售与业绩分析 - MySQL 数据落地")
        print("=" * 60)
        
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 先清理可能存在的旧数据
        print("\n[0/7] 清理旧数据...")
        for table in ['ads_branch_sales_ranking', 'dws_product_performance', 'dwd_product_sales_daily']:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()
        print("  OK")
        
        # 1. 创建 DWD 层表
        print("\n[1/6] 创建 DWD 层表: dwd_product_sales_daily")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dwd', 'dwd_product_sales_daily.sql'))
        conn.commit()
        print("  OK")
        
        # 2. 创建 DWS 层表
        print("\n[2/6] 创建 DWS 层表: dws_product_performance")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dws', 'dws_product_performance.sql'))
        conn.commit()
        print("  OK")
        
        # 3. 创建 ADS 层表
        print("\n[3/6] 创建 ADS 层表: ads_branch_sales_ranking")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_branch_sales_ranking.sql'))
        conn.commit()
        print("  OK")
        
        # 4. 执行 ODS -> DWD ETL
        print("\n[4/6] 执行 ODS -> DWD ETL: dwd_product_sales_daily")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dwd_product_sales_daily.sql'))
        # Convert SQLite syntax to MySQL
        etl_sql = etl_sql.replace('INSERT OR REPLACE', 'INSERT')
        etl_sql = etl_sql.replace("DATETIME('now')", "NOW()")
        # Fix collation issues
        etl_sql = etl_sql.replace(
            "LEFT JOIN ods_product p ON t.product_id = p.product_id AND p.is_current = 1",
            "LEFT JOIN ods_product p ON t.product_id COLLATE utf8mb4_unicode_ci = p.product_id COLLATE utf8mb4_unicode_ci AND p.is_current = 1"
        )
        etl_sql = etl_sql.replace(
            "LEFT JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1",
            "LEFT JOIN ods_account a ON t.account_id COLLATE utf8mb4_unicode_ci = a.account_id COLLATE utf8mb4_unicode_ci AND a.is_current = 1"
        )
        # Handle duplicate keys
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 5. 执行 DWD -> DWS ETL
        print("\n[5/6] 执行 DWD -> DWS ETL: dws_product_performance")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dws_product_performance.sql'))
        etl_sql = etl_sql.replace('INSERT OR REPLACE', 'INSERT')
        etl_sql = etl_sql.replace("DATETIME('now')", "NOW()")
        # Fix collation issues
        etl_sql = etl_sql.replace(
            "LEFT JOIN ods_product p ON dwd.product_id = p.product_id AND p.is_current = 1",
            "LEFT JOIN ods_product p ON dwd.product_id COLLATE utf8mb4_unicode_ci = p.product_id COLLATE utf8mb4_unicode_ci AND p.is_current = 1"
        )
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 6. 执行 DWD+ODS -> ADS ETL
        print("\n[6/6] 执行 DWD+ODS -> ADS ETL: ads_branch_sales_ranking")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_branch_sales_ranking.sql'))
        etl_sql = etl_sql.replace('INSERT OR REPLACE', 'INSERT')
        etl_sql = etl_sql.replace("DATETIME('now')", "NOW()")
        # Fix collation issues
        etl_sql = etl_sql.replace(
            "LEFT JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1",
            "LEFT JOIN ods_account a ON t.account_id COLLATE utf8mb4_unicode_ci = a.account_id COLLATE utf8mb4_unicode_ci AND a.is_current = 1"
        )
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 验证数据
        print("\n" + "=" * 60)
        print("MySQL 数据验证")
        print("=" * 60)
        
        # DWD 验证
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
        
        # DWS 验证
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
        
        # ADS 验证
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
        
        # 统计各表总行数
        print("\n" + "=" * 60)
        print("数据量统计")
        print("=" * 60)
        for table in ['dwd_product_sales_daily', 'dws_product_performance', 'ads_branch_sales_ranking']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} 行")
        
        # 验证中文注释
        print("\n" + "=" * 60)
        print("MySQL 中文注释验证")
        print("=" * 60)
        for table in ['dwd_product_sales_daily', 'dws_product_performance', 'ads_branch_sales_ranking']:
            print(f"\n表: {table}")
            verify_comments(cursor, table)
        
        conn.close()
        print("\n" + "=" * 60)
        print("MySQL 数据落地完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
