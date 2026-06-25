import pymysql
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

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 选项B指标定义
METRICS = [
    # DWD层指标
    ('M101', '产品日申购金额', 'product_daily_purchase_amount', '每日各产品的申购金额汇总', "SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END)", '日', 'dwd_product_sales_daily', 'ods_transaction'),
    ('M102', '产品日赎回金额', 'product_daily_redemption_amount', '每日各产品的赎回金额汇总', "SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END)", '日', 'dwd_product_sales_daily', 'ods_transaction'),
    ('M103', '产品日净申购金额', 'product_daily_net_purchase_amount', '每日各产品净申购金额（申购-赎回）', '申购金额 - 赎回金额', '日', 'dwd_product_sales_daily', 'dwd_product_sales_daily'),
    ('M104', '产品日申购笔数', 'product_daily_purchase_count', '每日各产品的申购交易笔数', 'COUNT(purchase交易)', '日', 'dwd_product_sales_daily', 'ods_transaction'),
    ('M105', '产品日赎回笔数', 'product_daily_redemption_count', '每日各产品的赎回交易笔数', 'COUNT(redemption交易)', '日', 'dwd_product_sales_daily', 'ods_transaction'),
    ('M106', '产品日交易客户数', 'product_daily_customer_count', '每日各产品的交易客户数（去重）', 'COUNT(DISTINCT customer_id)', '日', 'dwd_product_sales_daily', 'ods_transaction'),
    ('M107', '产品日总手续费', 'product_daily_total_fee', '每日各产品的手续费汇总', 'SUM(fee)', '日', 'dwd_product_sales_daily', 'ods_transaction'),
    # DWS层指标
    ('M201', '产品累计销售金额', 'product_total_sales_amount', '各产品自发行以来的累计销售金额', 'SUM(purchase_amount) OVER (PARTITION BY product_id ORDER BY stat_date)', '日', 'dws_product_performance', 'dwd_product_sales_daily'),
    ('M202', '产品累计赎回金额', 'product_total_redemption_amount', '各产品自发行以来的累计赎回金额', 'SUM(redemption_amount) OVER (PARTITION BY product_id ORDER BY stat_date)', '日', 'dws_product_performance', 'dwd_product_sales_daily'),
    ('M203', '产品净销售金额', 'product_net_sales_amount', '各产品累计净销售金额', '累计销售金额 - 累计赎回金额', '日', 'dws_product_performance', 'dws_product_performance'),
    ('M204', '产品累计交易客户数', 'product_total_customer_count', '各产品累计交易客户数', 'SUM(customer_count) OVER (PARTITION BY product_id ORDER BY stat_date)', '日', 'dws_product_performance', 'dwd_product_sales_daily'),
    ('M205', '产品日均销售额', 'product_avg_daily_sales', '各产品近7日日均销售额', 'AVG(purchase_amount) OVER (7日滑动窗口)', '日', 'dws_product_performance', 'dwd_product_sales_daily'),
    ('M206', '产品周销售额', 'product_weekly_sales_amount', '各产品近7日销售总额', 'SUM(purchase_amount) OVER (7日滑动窗口)', '周', 'dws_product_performance', 'dwd_product_sales_daily'),
    ('M207', '产品月销售额', 'product_monthly_sales_amount', '各产品近30日销售总额', 'SUM(purchase_amount) OVER (30日滑动窗口)', '月', 'dws_product_performance', 'dwd_product_sales_daily'),
    ('M208', '产品预期收益率', 'product_expected_return', '产品发行时设定的预期年化收益率', '取自ods_product.expected_return', '日', 'dws_product_performance', 'ods_product'),
    # ADS层指标
    ('M301', '网点日销售总额', 'branch_daily_sales_amount', '各网点每日销售总额', "SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END)", '日', 'ads_branch_sales_ranking', 'ods_transaction'),
    ('M302', '网点日赎回总额', 'branch_daily_redemption_amount', '各网点每日赎回总额', "SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END)", '日', 'ads_branch_sales_ranking', 'ods_transaction'),
    ('M303', '网点净销售额', 'branch_net_sales_amount', '各网点净销售额', '销售总额 - 赎回总额', '日', 'ads_branch_sales_ranking', 'ads_branch_sales_ranking'),
    ('M304', '网点日交易笔数', 'branch_daily_transaction_count', '各网点每日交易笔数', 'COUNT(transaction_id)', '日', 'ads_branch_sales_ranking', 'ods_transaction'),
    ('M305', '网点日交易客户数', 'branch_daily_customer_count', '各网点每日交易客户数（去重）', 'COUNT(DISTINCT customer_id)', '日', 'ads_branch_sales_ranking', 'ods_transaction'),
    ('M306', '网点销售排名', 'branch_sales_ranking', '各网点按销售额的排名', 'RANK() OVER (PARTITION BY stat_date ORDER BY total_sales_amount DESC)', '日', 'ads_branch_sales_ranking', 'ads_branch_sales_ranking'),
    ('M307', '网点销售占比', 'branch_sales_share', '各网点销售额占当日总销售额的比例', '网点销售额 / 当日总销售额', '日', 'ads_branch_sales_ranking', 'ads_branch_sales_ranking'),
]

def main():
    try:
        print("=" * 60)
        print("选项B: 指标元数据写入MySQL")
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
        
        # 创建表
        print("\n[1/2] 创建指标定义表...")
        cursor.execute("DROP TABLE IF EXISTS ads_metric_definition")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ads_metric_definition (
                metric_id VARCHAR(20) PRIMARY KEY COMMENT '指标编码',
                metric_name VARCHAR(100) COMMENT '指标名称',
                metric_name_en VARCHAR(100) COMMENT '指标英文名',
                metric_description TEXT COMMENT '指标描述',
                calculation_logic TEXT COMMENT '计算逻辑',
                update_frequency VARCHAR(20) COMMENT '更新频率',
                source_table VARCHAR(100) COMMENT '来源表',
                dm_src_info VARCHAR(100) COMMENT '数据来源表',
                owner VARCHAR(50) COMMENT '负责人',
                create_time DATETIME COMMENT '创建时间',
                update_time DATETIME COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标定义表'
        """)
        conn.commit()
        print("  OK")
        
        # 插入/更新指标数据
        print("\n[2/2] 写入指标数据...")
        cursor.execute("DELETE FROM ads_metric_definition WHERE metric_id LIKE 'M1%' OR metric_id LIKE 'M2%' OR metric_id LIKE 'M3%'")
        
        for metric in METRICS:
            cursor.execute("""
                INSERT INTO ads_metric_definition 
                (metric_id, metric_name, metric_name_en, metric_description, calculation_logic, 
                 update_frequency, source_table, dm_src_info, owner, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (*metric, 'data_team', now, now))
        
        conn.commit()
        print(f"  OK - 写入 {len(METRICS)} 条指标定义")
        
        # 验证
        print("\n" + "=" * 60)
        print("指标元数据验证")
        print("=" * 60)
        
        cursor.execute("SELECT metric_id, metric_name, source_table FROM ads_metric_definition ORDER BY metric_id")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:<25} 来源表: {row[2]}")
        
        conn.close()
        print("\n" + "=" * 60)
        print("指标元数据写入完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
