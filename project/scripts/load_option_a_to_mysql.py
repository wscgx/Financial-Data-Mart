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
        print("选项A: 客户资产价值分析体系 - MySQL 数据落地")
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
        print("\n[0/7] 清理旧数据...")
        for table in ['ads_customer_net_asset_change', 'ads_customer_value_level_dist',
                      'ads_customer_aum_ranking', 'ads_customer_aum_daily',
                      'dws_customer_value_profile', 'dwd_customer_asset_daily']:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()
        print("  OK")
        
        # 1-6. 创建表
        tables = [
            ('dwd', 'dwd_customer_asset_daily', 'DWD 层表'),
            ('dws', 'dws_customer_value_profile', 'DWS 层表'),
            ('ads', 'ads_customer_aum_daily', 'ADS 层表 - 客户AUM日指标'),
            ('ads', 'ads_customer_aum_ranking', 'ADS 层表 - 客户AUM排名'),
            ('ads', 'ads_customer_value_level_dist', 'ADS 层表 - 客户价值等级分布'),
            ('ads', 'ads_customer_net_asset_change', 'ADS 层表 - 客户资产净变动'),
        ]
        
        for i, (layer, table, desc) in enumerate(tables, 1):
            print(f"\n[{i}/6] 创建 {desc}: {table}")
            execute_ddl(cursor, os.path.join(SQL_DIR, layer, f'{table}.sql'))
            conn.commit()
            print("  OK")
        
        # 执行 ETL
        etl_files = [
            ('etl_dwd_customer_asset_daily.sql', 'ODS -> DWD', 'dwd_customer_asset_daily'),
            ('etl_dws_customer_value_profile.sql', 'DWD -> DWS', 'dws_customer_value_profile'),
            ('etl_ads_customer_aum_daily.sql', 'DWD -> ADS', 'ads_customer_aum_daily'),
            ('etl_ads_customer_aum_ranking.sql', 'DWS -> ADS', 'ads_customer_aum_ranking'),
            ('etl_ads_customer_value_level_dist.sql', 'DWS -> ADS', 'ads_customer_value_level_dist'),
            ('etl_ads_customer_net_asset_change.sql', 'DWD -> ADS', 'ads_customer_net_asset_change'),
        ]
        
        for i, (etl_file, desc, target_table) in enumerate(etl_files, 7):
            print(f"\n[{i}/12] 执行 {desc} ETL: {target_table}")
            etl_sql = read_sql_file(os.path.join(ETL_DIR, etl_file))
            cursor.execute(etl_sql)
            conn.commit()
            print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 验证数据
        print("\n" + "=" * 60)
        print("MySQL 数据验证")
        print("=" * 60)
        
        for table in ['dwd_customer_asset_daily', 'dws_customer_value_profile',
                      'ads_customer_aum_daily', 'ads_customer_aum_ranking',
                      'ads_customer_value_level_dist', 'ads_customer_net_asset_change']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} 行")
        
        # 验证中文注释
        print("\n" + "=" * 60)
        print("MySQL 中文注释验证")
        print("=" * 60)
        for table in ['dwd_customer_asset_daily', 'dws_customer_value_profile',
                      'ads_customer_aum_daily', 'ads_customer_aum_ranking',
                      'ads_customer_value_level_dist', 'ads_customer_net_asset_change']:
            print(f"\n表: {table}")
            verify_comments(cursor, table)
        
        # 验证 dm_src_info
        print("\n" + "=" * 60)
        print("dm_src_info 字段验证")
        print("=" * 60)
        for table in ['dwd_customer_asset_daily', 'dws_customer_value_profile',
                      'ads_customer_aum_daily', 'ads_customer_aum_ranking',
                      'ads_customer_value_level_dist', 'ads_customer_net_asset_change']:
            cursor.execute(f"SELECT dm_src_info, COUNT(*) FROM {table} GROUP BY dm_src_info LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"  {table}: 来源表 = {result[0]}")
        
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
