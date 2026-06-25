"""
将 ODS CSV 数据加载到 MySQL
"""
import pymysql
import csv
import os
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Config
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASS = '123456'
MYSQL_DB = 'financial_dw'

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
SQL_DIR = os.path.join(BASE_DIR, 'sql')
DATA_DIR = os.path.join(BASE_DIR, 'data', 'ods')

# ODS 表定义
ODS_TABLES = {
    'ods_customer': {
        'columns': ['customer_id', 'first_name', 'last_name', 'gender', 'birth_date',
                    'city', 'phone', 'email', 'registration_date', 'status'],
        'scd_columns': ['start_date', 'end_date', 'is_current'],
        'pk': 'customer_id',
    },
    'ods_account': {
        'columns': ['account_id', 'customer_id', 'account_type', 'currency', 'open_date',
                    'status', 'branch'],
        'scd_columns': ['start_date', 'end_date', 'is_current'],
        'pk': 'account_id',
    },
    'ods_product': {
        'columns': ['product_id', 'product_name', 'product_type', 'risk_level',
                    'min_investment', 'expected_return', 'launch_date', 'maturity_date',
                    'status', 'manager'],
        'scd_columns': ['start_date', 'end_date', 'is_current'],
        'pk': 'product_id',
    },
    'ods_transaction': {
        'columns': ['transaction_id', 'account_id', 'product_id', 'transaction_type',
                    'amount', 'price', 'quantity', 'transaction_date', 'fee', 'status'],
        'scd_columns': ['start_date', 'end_date', 'is_current'],
        'pk': 'transaction_id',
    },
    'ods_holding': {
        'columns': ['holding_id', 'account_id', 'product_id', 'quantity', 'avg_cost',
                    'market_value', 'profit_loss', 'as_of_date'],
        'scd_columns': ['start_date', 'end_date', 'is_current'],
        'pk': 'holding_id',
    },
    'ods_risk_assessment': {
        'columns': ['customer_id', 'assessment_date', 'risk_category', 'score',
                    'questionnaire_version', 'valid_until', 'status'],
        'scd_columns': ['start_date', 'end_date', 'is_current'],
        'pk': None,  # Composite key
    },
}


def read_sql_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def execute_ddl(cursor, filepath):
    """Execute DDL file"""
    sql = read_sql_file(filepath)
    lines = [line for line in sql.split('\n') if not line.strip().startswith('--')]
    clean_sql = '\n'.join(lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            if 'Duplicate key' not in str(e) and '1061' not in str(e):
                print(f"  DDL 警告: {e}")


def load_csv_to_mysql(cursor, table_name, csv_path, table_config):
    """Load CSV data to MySQL table"""
    if not os.path.exists(csv_path):
        print(f"  CSV 文件不存在: {csv_path}")
        return 0
    
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print(f"  CSV 文件为空: {csv_path}")
        return 0
    
    # Add SCD columns
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    all_columns = table_config['columns'] + table_config['scd_columns']
    
    # Build INSERT statement - use INSERT IGNORE to skip duplicates
    placeholders = ', '.join(['%s'] * len(all_columns))
    columns_str = ', '.join(all_columns)
    insert_sql = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    # Prepare data
    data = []
    for row in rows:
        values = [row.get(col, '') for col in table_config['columns']]
        # Add SCD values
        values.append(now)  # start_date
        values.append('9999-12-31')  # end_date
        values.append(1)  # is_current
        data.append(tuple(values))
    
    # Batch insert
    batch_size = 1000
    total_inserted = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        total_inserted += cursor.rowcount
    
    return total_inserted


def main():
    print("=" * 60)
    print("ODS 数据加载到 MySQL")
    print("=" * 60)
    
    # Connect to MySQL
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        database=MYSQL_DB,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # Create ODS tables
    print("\n[1] 创建 ODS 表结构...")
    for table_name in ODS_TABLES.keys():
        ddl_path = os.path.join(SQL_DIR, 'ods', f'{table_name}.sql')
        if os.path.exists(ddl_path):
            print(f"  创建 {table_name}...")
            execute_ddl(cursor, ddl_path)
            conn.commit()
    
    # Load data
    print("\n[2] 加载 ODS 数据...")
    total_records = 0
    
    for table_name, config in ODS_TABLES.items():
        csv_path = os.path.join(DATA_DIR, f'{table_name}.csv')
        print(f"\n  加载 {table_name}...")
        
        # Clear existing data
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
        
        # Load CSV
        count = load_csv_to_mysql(cursor, table_name, csv_path, config)
        conn.commit()
        total_records += count
        print(f"    ✓ 加载 {count:,} 条记录")
    
    # Summary
    print("\n" + "=" * 60)
    print("加载完成!")
    print("=" * 60)
    print(f"总计加载 {total_records:,} 条记录")
    
    # Verify
    print("\n[3] 验证数据...")
    for table_name in ODS_TABLES.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count:,} 条")
    
    conn.close()
    print("\n✓ ODS 数据加载完成!")


if __name__ == "__main__":
    main()
