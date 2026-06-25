import pymysql
import os
import csv
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
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ods')

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

def load_ods_risk_assessment(cursor):
    """Load ods_risk_assessment from CSV"""
    csv_path = os.path.join(DATA_DIR, 'ods_risk_assessment.csv')
    if not os.path.exists(csv_path):
        print("  警告: ods_risk_assessment.csv 不存在，跳过加载")
        return 0
    
    cursor.execute("DROP TABLE IF EXISTS ods_risk_assessment")
    cursor.execute("""
        CREATE TABLE ods_risk_assessment (
            customer_id VARCHAR(50) COMMENT '客户ID',
            assessment_date VARCHAR(20) COMMENT '测评日期',
            risk_category VARCHAR(20) COMMENT '风险等级',
            score DECIMAL(10,2) COMMENT '测评分数',
            questionnaire_version VARCHAR(20) COMMENT '问卷版本',
            valid_until VARCHAR(20) COMMENT '有效期至',
            status VARCHAR(20) COMMENT '状态',
            start_date VARCHAR(20) COMMENT '生效日期',
            end_date VARCHAR(20) COMMENT '失效日期',
            is_current INT DEFAULT 1 COMMENT '是否当前版本',
            etl_load_time DATETIME COMMENT 'ETL加载时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户风险测评表'
    """)
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO ods_risk_assessment 
                (customer_id, assessment_date, risk_category, score, questionnaire_version, 
                 valid_until, status, start_date, end_date, is_current, etl_load_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW())
            """, (
                row['customer_id'],
                row['assessment_date'],
                row['risk_category'],
                float(row['score']) if row['score'] else None,
                row['questionnaire_version'],
                row['valid_until'],
                row['status'],
                row.get('start_date', ''),
                row.get('end_date', ''),
            ))
            count += 1
    
    return count

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
        print("选项C: 客户风险匹配度分析 - MySQL 数据落地")
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
        
        # 加载 ODS 层 ods_risk_assessment
        print("\n[0/7] 加载 ODS 层: ods_risk_assessment")
        ods_count = load_ods_risk_assessment(cursor)
        conn.commit()
        print(f"  OK - 加载 {ods_count:,} 条记录")
        
        # 清理旧数据
        print("\n[1/9] 清理旧数据...")
        for table in ['ads_risk_metrics_daily', 'ads_risk_mismatch_alert', 'dws_risk_compliance_summary', 'dwd_customer_risk_match']:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        print("  OK")
        
        # 2. 创建 DWD 层表
        print("\n[2/9] 创建 DWD 层表: dwd_customer_risk_match")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dwd', 'dwd_customer_risk_match.sql'))
        conn.commit()
        print("  OK")
        
        # 3. 创建 DWS 层表
        print("\n[3/9] 创建 DWS 层表: dws_risk_compliance_summary")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'dws', 'dws_risk_compliance_summary.sql'))
        conn.commit()
        print("  OK")
        
        # 4. 创建 ADS 层表 - 预警清单
        print("\n[4/9] 创建 ADS 层表: ads_risk_mismatch_alert")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_risk_mismatch_alert.sql'))
        conn.commit()
        print("  OK")
        
        # 5. 创建 ADS 层表 - 指标汇总
        print("\n[5/9] 创建 ADS 层表: ads_risk_metrics_daily")
        execute_ddl(cursor, os.path.join(SQL_DIR, 'ads', 'ads_risk_metrics_daily.sql'))
        conn.commit()
        print("  OK")
        
        # 6. 执行 ODS -> DWD ETL
        print("\n[6/9] 执行 ODS -> DWD ETL: dwd_customer_risk_match")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dwd_customer_risk_match.sql'))
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 7. 执行 DWD -> DWS ETL
        print("\n[7/9] 执行 DWD -> DWS ETL: dws_risk_compliance_summary")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_dws_risk_compliance_summary.sql'))
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 8. 执行 DWD -> ADS ETL (预警清单)
        print("\n[8/9] 执行 DWD -> ADS ETL: ads_risk_mismatch_alert")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_risk_mismatch_alert.sql'))
        etl_sql = etl_sql.replace('INSERT INTO', 'INSERT IGNORE INTO')
        cursor.execute(etl_sql)
        conn.commit()
        print(f"  OK - 影响 {cursor.rowcount} 条记录")
        
        # 9. 执行指标 ETL
        print("\n[9/9] 执行指标 ETL: ads_risk_metrics_daily")
        etl_sql = read_sql_file(os.path.join(ETL_DIR, 'etl_ads_risk_metrics_daily.sql'))
        # Remove comment lines
        lines = [line for line in etl_sql.split('\n') if not line.strip().startswith('--')]
        clean_sql = '\n'.join(lines)
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
        total_rows = 0
        for stmt in statements:
            stmt = stmt.replace('INSERT IGNORE INTO', 'INSERT IGNORE INTO')
            if stmt:
                cursor.execute(stmt)
                total_rows += cursor.rowcount
        conn.commit()
        print(f"  OK - 影响 {total_rows} 条记录")
        
        # 验证数据
        print("\n" + "=" * 60)
        print("MySQL 数据验证")
        print("=" * 60)
        
        # DWD 验证
        cursor.execute("""
            SELECT stat_date, customer_id, product_name, product_risk_level, customer_risk_level, 
                   risk_match_flag, risk_gap, holding_market_value
            FROM dwd_customer_risk_match
            ORDER BY stat_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nDWD 层样例数据 (最近5条):")
            print(f"{'日期':<12} {'客户ID':<12} {'产品名称':<25} {'产品风险':<12} {'客户风险':<12} {'匹配':<10} {'差距':>6} {'市值':>15}")
            print("-" * 110)
            for row in rows:
                print(f"{row[0]:<12} {row[1]:<12} {row[2]:<25} {row[3]:<12} {row[4]:<12} {row[5]:<10} {row[6]:>6} {row[7]:>15,.2f}")
        else:
            print("\nDWD 层: 无数据")
        
        # DWS 验证
        cursor.execute("""
            SELECT stat_date, customer_id, customer_risk_level, total_holding_count, 
                   mismatch_holding_count, mismatch_ratio, compliance_status
            FROM dws_risk_compliance_summary
            ORDER BY stat_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nDWS 层样例数据 (最近5条):")
            print(f"{'日期':<12} {'客户ID':<12} {'客户风险':<12} {'总持仓':>6} {'错配':>6} {'错配率':>8} {'合规状态':<12}")
            print("-" * 80)
            for row in rows:
                risk_level = row[2] if row[2] else 'NULL'
                mismatch_ratio = row[5] if row[5] is not None else 0
                print(f"{row[0]:<12} {row[1]:<12} {risk_level:<12} {row[3]:>6} {row[4]:>6} {mismatch_ratio:>8.2%} {row[6]:<12}")
        else:
            print("\nDWS 层: 无数据")
        
        # ADS 验证
        cursor.execute("""
            SELECT stat_date, alert_id, customer_name, product_name, customer_risk_level, 
                   product_risk_level, risk_gap, alert_level, alert_type
            FROM ads_risk_mismatch_alert
            ORDER BY 
                CASE alert_level WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                risk_gap DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nADS 层预警清单 (前10条):")
            print(f"{'日期':<12} {'客户姓名':<15} {'产品名称':<25} {'客户风险':<12} {'产品风险':<12} {'差距':>6} {'级别':<8} {'类型':<10}")
            print("-" * 110)
            for row in rows:
                customer_name = row[2] if row[2] else 'NULL'
                product_name = row[3] if row[3] else 'NULL'
                customer_risk = row[4] if row[4] else 'NULL'
                product_risk = row[5] if row[5] else 'NULL'
                gap = row[6] if row[6] is not None else 0
                print(f"{row[0]:<12} {customer_name:<15} {product_name:<25} {customer_risk:<12} {product_risk:<12} {gap:>6} {row[7]:<8} {row[8]:<10}")
        else:
            print("\nADS 层: 无预警数据")
        
        # 统计各表总行数
        print("\n" + "=" * 60)
        print("数据量统计")
        print("=" * 60)
        for table in ['ods_risk_assessment', 'dwd_customer_risk_match', 'dws_risk_compliance_summary', 'ads_risk_mismatch_alert', 'ads_risk_metrics_daily']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} 行")
        
        # 风险指标展示
        print("\n" + "=" * 60)
        print("风险指标汇总 (最新日期)")
        print("=" * 60)
        cursor.execute("""
            SELECT stat_date, metric_name, metric_value, metric_type
            FROM ads_risk_metrics_daily
            WHERE stat_date = (SELECT MAX(stat_date) FROM ads_risk_metrics_daily)
            ORDER BY metric_name
        """)
        
        metric_names = {
            'risk_mismatch_customer_count': '风险错配客户数',
            'assessment_expired_rate': '测评过期率',
            'high_risk_product_holding_rate': '高风险产品持有率',
            'risk_mismatch_holding_count': '风险错配持仓数',
            'risk_mismatch_holding_market_value': '风险错配持仓市值',
            'compliance_customer_rate': '合规客户占比',
            'warning_customer_count': '预警客户数',
            'violation_customer_count': '违规客户数',
            'avg_risk_gap': '平均风险差距',
            'high_alert_count': '高风险预警数'
        }
        
        for row in cursor.fetchall():
            stat_date, metric_name, metric_value, metric_type = row
            display_name = metric_names.get(metric_name, metric_name)
            if metric_type == 'rate' and 'gap' not in metric_name:
                display_value = f"{metric_value:.2%}"
            elif metric_type == 'amount':
                display_value = f"{metric_value:,.2f}"
            else:
                display_value = f"{metric_value:,.2f}"
            print(f"  {display_name}: {display_value}")
        
        # 风险匹配统计
        print("\n" + "=" * 60)
        print("风险匹配统计")
        print("=" * 60)
        cursor.execute("""
            SELECT risk_match_flag, COUNT(*) as cnt, 
                   SUM(holding_market_value) as total_mv
            FROM dwd_customer_risk_match
            GROUP BY risk_match_flag
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,} 条, 持仓市值 {row[2]:,.2f}")
        
        # 合规状态统计
        print("\n合规状态统计:")
        cursor.execute("""
            SELECT compliance_status, COUNT(*) as cnt
            FROM dws_risk_compliance_summary
            GROUP BY compliance_status
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,} 客户")
        
        # 预警级别统计
        print("\n预警级别统计:")
        cursor.execute("""
            SELECT alert_level, COUNT(*) as cnt
            FROM ads_risk_mismatch_alert
            GROUP BY alert_level
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,} 条")
        
        # 验证中文注释
        print("\n" + "=" * 60)
        print("MySQL 中文注释验证")
        print("=" * 60)
        for table in ['ods_risk_assessment', 'dwd_customer_risk_match', 'dws_risk_compliance_summary', 'ads_risk_mismatch_alert', 'ads_risk_metrics_daily']:
            print(f"\n表: {table}")
            verify_comments(cursor, table)
        
        # 验证 dm_src_info
        print("\n" + "=" * 60)
        print("dm_src_info 字段验证")
        print("=" * 60)
        for table in ['dwd_customer_risk_match', 'dws_risk_compliance_summary', 'ads_risk_mismatch_alert', 'ads_risk_metrics_daily']:
            cursor.execute(f"SELECT DISTINCT dm_src_info FROM {table} LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"  {table}: 来源表 = {result[0]}")
        
        conn.close()
        print("\n" + "=" * 60)
        print("选项C: MySQL 数据落地完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
