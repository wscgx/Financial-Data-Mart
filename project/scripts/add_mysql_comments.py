import pymysql
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456', database='financial_dw', charset='utf8mb4')
cursor = conn.cursor()

print("📖 正在读取注释元数据...")
cursor.execute("SELECT table_name, column_name, comment_type, comment_text FROM table_comment_metadata")
comments = cursor.fetchall()

# 获取字段类型
cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'financial_dw'
""")
col_info = {}
for row in cursor.fetchall():
    col_info[(row[0], row[1])] = {
        'type': row[2],
        'nullable': 'NULL' if row[3] == 'YES' else 'NOT NULL',
        'default': f"DEFAULT {row[4]}" if row[4] is not None else ''
    }

print("🔧 正在应用注释...")
applied = 0

for table, col, ctype, text in comments:
    try:
        if ctype == 'table':
            sql = f"ALTER TABLE {table} COMMENT = '{text}'"
            cursor.execute(sql)
            applied += 1
        elif ctype == 'column':
            info = col_info.get((table, col))
            if info:
                # 构建 MODIFY 语句
                type_def = info['type']
                null_def = info['nullable']
                default_def = info['default']
                sql = f"ALTER TABLE {table} MODIFY {col} {type_def} {null_def} {default_def} COMMENT '{text}'"
                cursor.execute(sql)
                applied += 1
            else:
                print(f"  ⚠️ 未找到字段信息: {table}.{col}")
    except Exception as e:
        print(f"  ❌ 失败: {table}.{col} - {e}")

conn.commit()
print(f"\n✅ 成功应用 {applied} 条注释")

# 验证
print("\n🔍 验证表注释:")
cursor.execute("SHOW TABLE STATUS WHERE Name IN ('dwd_customer_asset_daily', 'dws_customer_value_profile', 'ads_customer_aum_ranking');")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[17]}")

print("\n🔍 验证字段注释 (dwd_customer_asset_daily):")
cursor.execute("""
    SELECT COLUMN_NAME, COLUMN_COMMENT 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'financial_dw' AND TABLE_NAME = 'dwd_customer_asset_daily'
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
