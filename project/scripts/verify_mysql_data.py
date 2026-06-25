import pymysql
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456', database='financial_dw', charset='utf8mb4')
cursor = conn.cursor()

print("=== MySQL 数据库验证 ===\n")

print("📋 表清单及行数:")
cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {t[0]};")
    count = cursor.fetchone()[0]
    print(f"  {t[0]}: {count} 行")

print("\n📊 客户价值等级分布:")
cursor.execute("SELECT level_name, customer_count, total_aum, aum_percentage FROM ads_customer_value_level_dist;")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} 人, AUM={row[2]:,.2f}, 占比={row[3]:.2f}%")

print("\n🏆 AUM 排名 TOP 5:")
cursor.execute("SELECT ranking, customer_name, total_aum, customer_value_level FROM ads_customer_aum_ranking ORDER BY ranking LIMIT 5;")
for row in cursor.fetchall():
    print(f"  #{row[0]} {row[1]}: {row[2]:,.2f} ({row[3]})")

conn.close()
print("\n✅ 验证完成！")
