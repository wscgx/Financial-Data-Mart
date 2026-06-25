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
        print("选项E: 综合财富管理驾驶舱 - MySQL 数据落地")
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
        print("\n[0/8] 清理旧数据...")
        for table in ['ads_anomaly_detection', 'ads_multi_dimension_analysis', 'ads_executive_dashboard', 'dws_platform_daily_summary']:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        print("  OK")
        
        # 1. 创建 DWS 层表
        print("\n[1/8] 创建 DWS 层表: dws_platform_daily_summary")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dws', 'dws_platform_daily_summary.sql'))
        conn.commit()
        print("  OK")
        
        # 2. 创建 ADS 层表 - 高管驾驶舱
        print("\n[2/8] 创建 ADS 层表: ads_executive_dashboard")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_executive_dashboard.sql'))
        conn.commit()
        print("  OK")
        
        # 3. 创建 ADS 层表 - 多维度交叉分析
        print("\n[3/8] 创建 ADS 层表: ads_multi_dimension_analysis")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_multi_dimension_analysis.sql'))
        conn.commit()
        print("  OK")
        
        # 4. 创建 ADS 层表 - 异常检测
        print("\n[4/8] 创建 ADS 层表: ads_anomaly_detection")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_anomaly_detection.sql'))
        conn.commit()
        print("  OK")
        
        # 5. 执行 ODS/DWD -> DWS ETL
        print("\n[5/8] 执行 ODS/DWD -> DWS ETL: dws_platform_daily_summary")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dws_platform_daily_summary.sql'))
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 6. 执行 DWS -> ADS ETL (高管驾驶舱)
        print("\n[6/8] 执行 DWS -> ADS ETL: ads_executive_dashboard")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_executive_dashboard.sql'))
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 7. 执行 ODS/DWD -> ADS ETL (多维度交叉分析)
        print("\n[7/8] 执行 ODS/DWD -> ADS ETL: ads_multi_dimension_analysis")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_multi_dimension_analysis.sql'))
        # Remove comment lines
        lines = [line for line in etl_sql.split('\n') if not line.strip().startswith('--')]
        clean_sql = '\n'.join(lines)
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
        total_rows = 0
        for stmt in statements:
            if stmt:
                cursor.execute(stmt)
                total_rows += cursor.rowcount
        conn.commit()
        print(f"  OK - 影响 {total_rows} 条记录")
        
        # 8. 执行 DWS -> ADS ETL (异常检测)
        print("\n[8/8] 执行 DWS -> ADS ETL: ads_anomaly_detection")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_anomaly_detection.sql'))
        # Remove comment lines
        lines = [line for line in etl_sql.split('\n') if not line.strip().startswith('--')]
        clean_sql = '\n'.join(lines)
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
        total_rows = 0
        for stmt in statements:
            if stmt:
                cursor.execute(stmt)
                total_rows += cursor.rowcount
        conn.commit()
        print(f"  OK - 影响 {total_rows} 条记录")
        
        # 验证数据
        print("\n" + "=" * 60)
        print("MySQL 数据验证")
        print("=" * 60)
        
        # DWS 验证
        cursor.execute("""
            SELECT stat_date, total_customers, active_customers, total_aum, net_purchase_amount, product_coverage_rate
            FROM dws_platform_daily_summary
            ORDER BY stat_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nDWS 层样例数据 (最近5条):")
            print(f"{'日期':<12} {'总客户':>8} {'活跃':>8} {'总AUM':>15} {'净申购':>15} {'覆盖率':>8}")
            print("-" * 80)
            for row in rows:
                coverage = row[5] if row[5] is not None else 0
                print(f"{row[0]:<12} {row[1]:>8,} {row[2]:>8,} {row[3]:>15,.2f} {row[4]:>15,.2f} {coverage:>8.2%}")
        else:
            print("\nDWS 层: 无数据 (可能依赖的DWD层数据为空)")
        
        # ADS 高管驾驶舱验证
        cursor.execute("""
            SELECT stat_date, report_type, total_customers, total_aum, aum_growth_rate, transaction_conversion_rate
            FROM ads_executive_dashboard
            ORDER BY stat_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nADS 高管驾驶舱样例数据 (最近5条):")
            print(f"{'日期':<12} {'类型':<8} {'总客户':>8} {'总AUM':>15} {'AUM增长':>10} {'转化率':>8}")
            print("-" * 80)
            for row in rows:
                aum_growth = row[4] if row[4] is not None else 0
                conv_rate = row[5] if row[5] is not None else 0
                print(f"{row[0]:<12} {row[1]:<8} {row[2]:>8,} {row[3]:>15,.2f} {aum_growth:>10.2%} {conv_rate:>8.2%}")
        else:
            print("\nADS 高管驾驶舱: 无数据")
        
        # ADS 多维度分析验证
        cursor.execute("""
            SELECT stat_date, dimension_type, dimension_value, customer_count, aum
            FROM ads_multi_dimension_analysis
            ORDER BY stat_date DESC, dimension_type, customer_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nADS 多维度分析样例数据 (最近10条):")
            print(f"{'日期':<12} {'维度':<15} {'维度值':<20} {'客户数':>8} {'AUM':>15}")
            print("-" * 80)
            for row in rows:
                print(f"{row[0]:<12} {row[1]:<15} {row[2]:<20} {row[3]:>8,} {row[4]:>15,.2f}")
        else:
            print("\nADS 多维度分析: 无数据")
        
        # ADS 异常检测验证
        cursor.execute("""
            SELECT stat_date, anomaly_type, anomaly_level, current_value, deviation_rate
            FROM ads_anomaly_detection
            ORDER BY stat_date DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nADS 异常检测样例数据 (最近10条):")
            print(f"{'日期':<12} {'异常类型':<25} {'级别':<8} {'当前值':>15} {'偏差率':>10}")
            print("-" * 80)
            for row in rows:
                deviation = row[4] if row[4] is not None else 0
                print(f"{row[0]:<12} {row[1]:<25} {row[2]:<8} {row[3]:>15,.2f} {deviation:>10.2%}")
        else:
            print("\nADS 异常检测: 无异常数据 (正常)")
        
        # 统计各表总行数
        print("\n" + "=" * 60)
        print("数据量统计")
        print("=" * 60)
        for table in ['dws_platform_daily_summary', 'ads_executive_dashboard', 'ads_multi_dimension_analysis', 'ads_anomaly_detection']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} 行")
        
        # 验证中文注释
        print("\n" + "=" * 60)
        print("MySQL 中文注释验证")
        print("=" * 60)
        for table in ['dws_platform_daily_summary', 'ads_executive_dashboard', 'ads_multi_dimension_analysis', 'ads_anomaly_detection']:
            print(f"\n表: {table}")
            verify_comments(cursor, table)
        
        # 验证 dm_src_info
        print("\n" + "=" * 60)
        print("dm_src_info 字段验证")
        print("=" * 60)
        for table in ['dws_platform_daily_summary', 'ads_executive_dashboard', 'ads_multi_dimension_analysis', 'ads_anomaly_detection']:
            cursor.execute(f"SELECT DISTINCT dm_src_info FROM {table} LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"  {table}: 来源表 = {result[0]}")
        
        conn.close()
        print("\n" + "=" * 60)
        print("选项E: MySQL 数据落地完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
