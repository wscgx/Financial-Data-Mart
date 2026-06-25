import pymysql
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='password01.',
        charset='utf8mb4'
    )
    print("✅ 连接成功！")
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION();")
    version = cursor.fetchone()
    print(f"MySQL 版本: {version[0]}")
    
    cursor.execute("SHOW DATABASES;")
    print("\n=== 现有数据库 ===")
    for db in cursor.fetchall():
        print(f"  - {db[0]}")
        
    # 创建项目数据库
    cursor.execute("CREATE DATABASE IF NOT EXISTS financial_dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("\n✅ 已创建数据库: financial_dw")
    
    conn.close()
    print("\n连接已关闭。")
except Exception as e:
    print(f"❌ 连接失败: {e}")
