import csv
import os

MAPPING_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'mapping', 'option_b')
os.makedirs(MAPPING_DIR, exist_ok=True)

def write_mapping_csv(filename, header_info, columns, etl_info):
    """Write mapping CSV with UTF-8-BOM encoding"""
    filepath = os.path.join(MAPPING_DIR, filename)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        
        # Part 1: Basic info
        writer.writerow(['字段', '值'])
        for k, v in header_info.items():
            writer.writerow([k, v])
        
        # Empty row
        writer.writerow([])
        
        # Part 2: Column structure
        writer.writerow(['字段名', '数据类型', '中文注释', '是否主键', '是否可空', '默认值', '计算逻辑'])
        for col in columns:
            writer.writerow([
                col.get('name', ''),
                col.get('type', ''),
                col.get('comment', ''),
                '是' if col.get('pk', False) else '否',
                '否' if col.get('not_null', True) else '是',
                col.get('default', ''),
                col.get('calc_logic', '')
            ])
        
        # Empty row
        writer.writerow([])
        
        # Part 3: ETL logic
        writer.writerow(['加工逻辑项', '说明'])
        for k, v in etl_info.items():
            writer.writerow([k, v])
    
    print(f"  OK: {filepath}")

# DWD: dwd_product_sales_daily
write_mapping_csv(
    'mapping_dwd_product_sales_daily.csv',
    {
        '需求名称': '产品销售与业绩分析',
        '需求标识': 'option_b',
        '表名': 'dwd_product_sales_daily',
        '中文表名': '产品销售日汇总表',
        '层级': 'DWD',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'product_id', 'type': 'VARCHAR(50)', 'comment': '产品ID', 'pk': True, 'not_null': True},
        {'name': 'product_name', 'type': 'VARCHAR(100)', 'comment': '产品名称'},
        {'name': 'product_type', 'type': 'VARCHAR(50)', 'comment': '产品类型'},
        {'name': 'purchase_amount', 'type': 'DECIMAL(18,2)', 'comment': '申购金额', 'calc_logic': "SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END)"},
        {'name': 'redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '赎回金额', 'calc_logic': "SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END)"},
        {'name': 'net_purchase_amount', 'type': 'DECIMAL(18,2)', 'comment': '净申购金额', 'calc_logic': 'purchase_amount - redemption_amount'},
        {'name': 'purchase_count', 'type': 'INT', 'comment': '申购笔数', 'calc_logic': 'COUNT(purchase交易)'},
        {'name': 'redemption_count', 'type': 'INT', 'comment': '赎回笔数', 'calc_logic': 'COUNT(redemption交易)'},
        {'name': 'customer_count', 'type': 'INT', 'comment': '交易客户数', 'calc_logic': 'COUNT(DISTINCT customer_id)'},
        {'name': 'total_fee', 'type': 'DECIMAL(18,2)', 'comment': '总手续费', 'calc_logic': 'SUM(fee)'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'ods_transaction'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'ods_transaction, ods_product, ods_account',
        '关联条件': 'ods_transaction.product_id = ods_product.product_id AND ods_transaction.account_id = ods_account.account_id',
        '过滤条件': "transaction_type IN ('purchase', 'redemption') AND is_current = 1",
        '聚合粒度': 'transaction_date + product_id',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_dwd_product_sales_daily.sql'
    }
)

# DWS: dws_product_performance
write_mapping_csv(
    'mapping_dws_product_performance.csv',
    {
        '需求名称': '产品销售与业绩分析',
        '需求标识': 'option_b',
        '表名': 'dws_product_performance',
        '中文表名': '产品业绩宽表',
        '层级': 'DWS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'product_id', 'type': 'VARCHAR(50)', 'comment': '产品ID', 'pk': True, 'not_null': True},
        {'name': 'product_name', 'type': 'VARCHAR(100)', 'comment': '产品名称'},
        {'name': 'product_type', 'type': 'VARCHAR(50)', 'comment': '产品类型'},
        {'name': 'risk_level', 'type': 'VARCHAR(30)', 'comment': '风险等级'},
        {'name': 'manager', 'type': 'VARCHAR(50)', 'comment': '基金经理'},
        {'name': 'total_sales_amount', 'type': 'DECIMAL(18,2)', 'comment': '累计销售金额', 'calc_logic': 'SUM(purchase_amount) OVER (PARTITION BY product_id ORDER BY stat_date)'},
        {'name': 'total_redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '累计赎回金额', 'calc_logic': 'SUM(redemption_amount) OVER (PARTITION BY product_id ORDER BY stat_date)'},
        {'name': 'net_sales_amount', 'type': 'DECIMAL(18,2)', 'comment': '净销售金额', 'calc_logic': 'SUM(net_purchase_amount) OVER (PARTITION BY product_id ORDER BY stat_date)'},
        {'name': 'total_customer_count', 'type': 'INT', 'comment': '累计交易客户数', 'calc_logic': 'SUM(customer_count) OVER (PARTITION BY product_id ORDER BY stat_date)'},
        {'name': 'avg_daily_sales', 'type': 'DECIMAL(18,2)', 'comment': '日均销售额', 'calc_logic': 'AVG(purchase_amount) OVER (7日滑动窗口)'},
        {'name': 'weekly_sales_amount', 'type': 'DECIMAL(18,2)', 'comment': '本周销售额', 'calc_logic': 'SUM(purchase_amount) OVER (7日滑动窗口)'},
        {'name': 'monthly_sales_amount', 'type': 'DECIMAL(18,2)', 'comment': '本月销售额', 'calc_logic': 'SUM(purchase_amount) OVER (30日滑动窗口)'},
        {'name': 'expected_return', 'type': 'DECIMAL(8,4)', 'comment': '预期收益率'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'dwd_product_sales_daily'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'dwd_product_sales_daily, ods_product',
        '关联条件': 'dwd_product_sales_daily.product_id = ods_product.product_id',
        '过滤条件': 'stat_date IS NOT NULL',
        '聚合粒度': 'stat_date + product_id',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_dws_product_performance.sql'
    }
)

# ADS: ads_branch_sales_ranking
write_mapping_csv(
    'mapping_ads_branch_sales_ranking.csv',
    {
        '需求名称': '产品销售与业绩分析',
        '需求标识': 'option_b',
        '表名': 'ads_branch_sales_ranking',
        '中文表名': '网点销售排名表',
        '层级': 'ADS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'branch', 'type': 'VARCHAR(50)', 'comment': '网点名称', 'pk': True, 'not_null': True},
        {'name': 'total_sales_amount', 'type': 'DECIMAL(18,2)', 'comment': '销售总额', 'calc_logic': "SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END)"},
        {'name': 'total_redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '赎回总额', 'calc_logic': "SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END)"},
        {'name': 'net_sales_amount', 'type': 'DECIMAL(18,2)', 'comment': '净销售额', 'calc_logic': 'total_sales_amount - total_redemption_amount'},
        {'name': 'transaction_count', 'type': 'INT', 'comment': '交易笔数', 'calc_logic': 'COUNT(transaction_id)'},
        {'name': 'customer_count', 'type': 'INT', 'comment': '交易客户数', 'calc_logic': 'COUNT(DISTINCT customer_id)'},
        {'name': 'sales_ranking', 'type': 'INT', 'comment': '销售排名', 'calc_logic': 'RANK() OVER (PARTITION BY stat_date ORDER BY total_sales_amount DESC)'},
        {'name': 'sales_share', 'type': 'DECIMAL(8,4)', 'comment': '销售占比', 'calc_logic': 'total_sales_amount / SUM(total_sales_amount) OVER (PARTITION BY stat_date)'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'ods_transaction'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'ods_transaction, ods_account',
        '关联条件': 'ods_transaction.account_id = ods_account.account_id',
        '过滤条件': "transaction_type IN ('purchase', 'redemption') AND is_current = 1",
        '聚合粒度': 'transaction_date + branch',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_ads_branch_sales_ranking.sql'
    }
)

print("\n所有 Mapping CSV 文件已生成（UTF-8-BOM编码）")
