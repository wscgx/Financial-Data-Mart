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
    lines = [line for line in sql.split('\n') if not line.strip().startswith('--')]
    clean_sql = '\n'.join(lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    
    table_name = None
    for stmt in statements:
        if 'CREATE TABLE' in stmt.upper():
            import re
            match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', stmt, re.IGNORECASE)
            if match:
                table_name = match.group(1)
            break
    
    if table_name:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            if 'Duplicate key' not in str(e) and '1061' not in str(e):
                raise

def verify_comments(cursor, table_name):
    """Verify table and column comments in MySQL"""
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
        print("选项D: 客户交易行为分析 - MySQL 数据落地")
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
        
        # 清理旧数据
        print("\n[0/6] 清理旧数据...")
        for table in ['ads_customer_churn_warning', 'dws_customer_behavior_profile', 'dwd_customer_activity_daily']:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        print("  OK")
        
        # 1. 创建 DWD 层表
        print("\n[1/6] 创建 DWD 层表: dwd_customer_activity_daily")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dwd', 'dwd_customer_activity_daily.sql'))
        conn.commit()
        print("  OK")
        
        # 2. 创建 DWS 层表
        print("\n[2/6] 创建 DWS 层表: dws_customer_behavior_profile")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dws', 'dws_customer_behavior_profile.sql'))
        conn.commit()
        print("  OK")
        
        # 3. 创建 ADS 层表
        print("\n[3/6] 创建 ADS 层表: ads_customer_churn_warning")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_customer_churn_warning.sql'))
        conn.commit()
        print("  OK")
        
        # 4. 执行 ODS -> DWD ETL
        print("\n[4/6] 执行 ODS -> DWD ETL: dwd_customer_activity_daily")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dwd_customer_activity_daily.sql'))
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 5. 执行 DWD -> DWS ETL
        print("\n[5/6] 执行 DWD -> DWS ETL: dws_customer_behavior_profile")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dws_customer_behavior_profile.sql'))
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 6. 执行 DWS -> ADS ETL
        print("\n[6/6] 执行 DWS -> ADS ETL: ads_customer_churn_warning")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_customer_churn_warning.sql'))
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
            SELECT stat_date, customer_id, transaction_count, purchase_amount, redemption_amount, net_amount
            FROM dwd_customer_activity_daily
            ORDER BY stat_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nDWD 层样例数据 (最近5条):")
            print(f"{'日期':<12} {'客户ID':<12} {'交易笔数':>8} {'申购金额':>12} {'赎回金额':>12} {'净额':>12}")
            print("-" * 80)
            for row in rows:
                print(f"{row[0]:<12} {row[1]:<12} {row[2]:>8} {row[3]:>12,.2f} {row[4]:>12,.2f} {row[5]:>12,.2f}")
        else:
            print("\nDWD 层: 无数据")
        
        # DWS 验证
        cursor.execute("""
            SELECT stat_date, customer_id, customer_name, total_transaction_count, 
                   transaction_frequency, churn_risk_level, asset_trend
            FROM dws_customer_behavior_profile
            ORDER BY stat_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nDWS 层样例数据 (最近5条):")
            print(f"{'日期':<12} {'客户ID':<12} {'客户姓名':<15} {'交易笔数':>8} {'频率':>8} {'流失风险':<10} {'资产趋势':<10}")
            print("-" * 90)
            for row in rows:
                freq = row[4] if row[4] is not None else 0
                print(f"{row[0]:<12} {row[1]:<12} {row[2]:<15} {row[3]:>8} {freq:>8.2f} {row[5]:<10} {row[6]:<10}")
        else:
            print("\nDWS 层: 无数据")
        
        # ADS 验证
        cursor.execute("""
            SELECT stat_date, customer_name, days_inactive, churn_risk_level, churn_risk_score, asset_trend
            FROM ads_customer_churn_warning
            ORDER BY churn_risk_score DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nADS 层流失预警 (前10条):")
            print(f"{'日期':<12} {'客户姓名':<15} {'未交易天数':>10} {'风险等级':<10} {'风险评分':>8} {'资产趋势':<10}")
            print("-" * 80)
            for row in rows:
                print(f"{row[0]:<12} {row[1]:<15} {row[2]:>10} {row[3]:<10} {row[4]:>8.2f} {row[5]:<10}")
        else:
            print("\nADS 层: 无预警数据")
        
        # 统计各表总行数
        print("\n" + "=" * 60)
        print("数据量统计")
        print("=" * 60)
        for table in ['dwd_customer_activity_daily', 'dws_customer_behavior_profile', 'ads_customer_churn_warning']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} 行")
        
        # 流失风险统计
        print("\n" + "=" * 60)
        print("流失风险统计")
        print("=" * 60)
        cursor.execute("""
            SELECT churn_risk_level, COUNT(*) as cnt
            FROM dws_customer_behavior_profile
            GROUP BY churn_risk_level
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,} 客户")
        
        # 资产趋势统计
        print("\n资产趋势统计:")
        cursor.execute("""
            SELECT asset_trend, COUNT(*) as cnt
            FROM dws_customer_behavior_profile
            GROUP BY asset_trend
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,} 客户")
        
        # 验证中文注释
        print("\n" + "=" * 60)
        print("MySQL 中文注释验证")
        print("=" * 60)
        for table in ['dwd_customer_activity_daily', 'dws_customer_behavior_profile', 'ads_customer_churn_warning']:
            print(f"\n表: {table}")
            verify_comments(cursor, table)
        
        # 验证 dm_src_info
        print("\n" + "=" * 60)
        print("dm_src_info 字段验证")
        print("=" * 60)
        for table in ['dwd_customer_activity_daily', 'dws_customer_behavior_profile', 'ads_customer_churn_warning']:
            cursor.execute(f"SELECT DISTINCT dm_src_info FROM {table} LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"  {table}: 来源表 = {result[0]}")
        
        conn.close()
        print("\n" + "=" * 60)
        print("选项D: MySQL 数据落地完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
