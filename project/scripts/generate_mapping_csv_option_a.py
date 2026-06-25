import csv
import os

MAPPING_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'mapping', 'option_a')
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

# DWD: dwd_customer_asset_daily
write_mapping_csv(
    'mapping_dwd_customer_asset_daily.csv',
    {
        '需求名称': '客户资产价值分析体系',
        '需求标识': 'option_a',
        '表名': 'dwd_customer_asset_daily',
        '中文表名': '客户资产日快照表',
        '层级': 'DWD',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'customer_id', 'type': 'VARCHAR(50)', 'comment': '客户ID', 'pk': True, 'not_null': True},
        {'name': 'account_id', 'type': 'VARCHAR(50)', 'comment': '账户ID', 'pk': True, 'not_null': True},
        {'name': 'holding_market_value', 'type': 'DECIMAL(18,2)', 'comment': '持仓市值', 'calc_logic': 'COALESCE(h.market_value, 0)'},
        {'name': 'purchase_amount', 'type': 'DECIMAL(18,2)', 'comment': '申购金额', 'calc_logic': "SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END)"},
        {'name': 'redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '赎回金额', 'calc_logic': "SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END)"},
        {'name': 'profit_loss', 'type': 'DECIMAL(18,2)', 'comment': '盈亏', 'calc_logic': 'COALESCE(h.profit_loss, 0)'},
        {'name': 'net_asset_change', 'type': 'DECIMAL(18,2)', 'comment': '资产净变动', 'calc_logic': 'purchase_amount - redemption_amount + profit_loss'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'ods_holding'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'ods_holding, ods_account, ods_transaction',
        '关联条件': 'ods_holding.account_id = ods_account.account_id AND ods_holding.account_id = ods_transaction.account_id',
        '过滤条件': 'ods_holding.is_current = 1 AND ods_account.is_current = 1',
        '聚合粒度': 'as_of_date + customer_id + account_id',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_dwd_customer_asset_daily.sql'
    }
)

# DWS: dws_customer_value_profile
write_mapping_csv(
    'mapping_dws_customer_value_profile.csv',
    {
        '需求名称': '客户资产价值分析体系',
        '需求标识': 'option_a',
        '表名': 'dws_customer_value_profile',
        '中文表名': '客户价值画像宽表',
        '层级': 'DWS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'customer_id', 'type': 'VARCHAR(50)', 'comment': '客户ID', 'pk': True, 'not_null': True},
        {'name': 'first_name', 'type': 'VARCHAR(50)', 'comment': '名'},
        {'name': 'last_name', 'type': 'VARCHAR(50)', 'comment': '姓'},
        {'name': 'city', 'type': 'VARCHAR(50)', 'comment': '城市'},
        {'name': 'total_aum', 'type': 'DECIMAL(18,2)', 'comment': '总资产规模', 'calc_logic': 'SUM(holding_market_value)'},
        {'name': 'customer_value_level', 'type': 'VARCHAR(30)', 'comment': '客户价值等级', 'calc_logic': 'CASE WHEN total_aum >= 1000000 THEN high_net_worth WHEN >= 100000 THEN middle ELSE regular END'},
        {'name': 'daily_aum', 'type': 'DECIMAL(18,2)', 'comment': '当日AUM', 'calc_logic': 'SUM(holding_market_value)'},
        {'name': 'avg_daily_aum_30d', 'type': 'DECIMAL(18,2)', 'comment': '30日日均AUM', 'calc_logic': 'AVG(total_aum) OVER 30天窗口'},
        {'name': 'avg_daily_aum_90d', 'type': 'DECIMAL(18,2)', 'comment': '90日日均AUM', 'calc_logic': 'AVG(total_aum) OVER 90天窗口'},
        {'name': 'aum_change_30d', 'type': 'DECIMAL(18,2)', 'comment': '30日AUM变动', 'calc_logic': '当前total_aum - 30天前total_aum'},
        {'name': 'total_purchase_amount', 'type': 'DECIMAL(18,2)', 'comment': '总申购金额', 'calc_logic': 'SUM(purchase_amount)'},
        {'name': 'total_redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '总赎回金额', 'calc_logic': 'SUM(redemption_amount)'},
        {'name': 'total_profit_loss', 'type': 'DECIMAL(18,2)', 'comment': '总盈亏', 'calc_logic': 'SUM(profit_loss)'},
        {'name': 'net_asset_change', 'type': 'DECIMAL(18,2)', 'comment': '资产净变动', 'calc_logic': 'SUM(net_asset_change)'},
        {'name': 'account_count', 'type': 'INT', 'comment': '账户数', 'calc_logic': 'COUNT(DISTINCT account_id)'},
        {'name': 'holding_product_count', 'type': 'INT', 'comment': '持仓产品数', 'calc_logic': 'COUNT(*)'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'dwd_customer_asset_daily'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'dwd_customer_asset_daily, ods_customer',
        '关联条件': 'dwd.customer_id = ods_customer.customer_id',
        '过滤条件': 'ods_customer.is_current = 1',
        '聚合粒度': 'stat_date + customer_id',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_dws_customer_value_profile.sql'
    }
)

# ADS: ads_customer_aum_daily
write_mapping_csv(
    'mapping_ads_customer_aum_daily.csv',
    {
        '需求名称': '客户资产价值分析体系',
        '需求标识': 'option_a',
        '表名': 'ads_customer_aum_daily',
        '中文表名': '客户AUM日指标表',
        '层级': 'ADS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'customer_id', 'type': 'VARCHAR(50)', 'comment': '客户ID', 'pk': True, 'not_null': True},
        {'name': 'customer_name', 'type': 'VARCHAR(100)', 'comment': '客户姓名', 'calc_logic': "CONCAT(first_name, ' ', last_name)"},
        {'name': 'city', 'type': 'VARCHAR(50)', 'comment': '城市'},
        {'name': 'holding_market_value', 'type': 'DECIMAL(18,2)', 'comment': '持仓市值'},
        {'name': 'cash_balance', 'type': 'DECIMAL(18,2)', 'comment': '现金余额', 'calc_logic': '0.0'},
        {'name': 'total_aum', 'type': 'DECIMAL(18,2)', 'comment': '总资产规模', 'calc_logic': 'holding_market_value'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'dwd_customer_asset_daily'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'dwd_customer_asset_daily, ods_customer',
        '关联条件': 'dwd.customer_id = ods_customer.customer_id',
        '过滤条件': 'stat_date = MAX(stat_date)',
        '聚合粒度': 'stat_date + customer_id',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_ads_customer_aum_daily.sql'
    }
)

# ADS: ads_customer_aum_ranking
write_mapping_csv(
    'mapping_ads_customer_aum_ranking.csv',
    {
        '需求名称': '客户资产价值分析体系',
        '需求标识': 'option_a',
        '表名': 'ads_customer_aum_ranking',
        '中文表名': '客户AUM排名表',
        '层级': 'ADS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'ranking', 'type': 'INT', 'comment': '排名', 'pk': True, 'not_null': True, 'calc_logic': 'ROW_NUMBER() OVER (ORDER BY total_aum DESC)'},
        {'name': 'customer_id', 'type': 'VARCHAR(50)', 'comment': '客户ID'},
        {'name': 'customer_name', 'type': 'VARCHAR(100)', 'comment': '客户姓名', 'calc_logic': "CONCAT(first_name, ' ', last_name)"},
        {'name': 'city', 'type': 'VARCHAR(50)', 'comment': '城市'},
        {'name': 'total_aum', 'type': 'DECIMAL(18,2)', 'comment': '总资产规模'},
        {'name': 'customer_value_level', 'type': 'VARCHAR(30)', 'comment': '客户价值等级'},
        {'name': 'avg_daily_aum_30d', 'type': 'DECIMAL(18,2)', 'comment': '30日日均AUM'},
        {'name': 'total_purchase_amount', 'type': 'DECIMAL(18,2)', 'comment': '总申购金额'},
        {'name': 'total_redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '总赎回金额'},
        {'name': 'total_profit_loss', 'type': 'DECIMAL(18,2)', 'comment': '总盈亏'},
        {'name': 'net_asset_change', 'type': 'DECIMAL(18,2)', 'comment': '资产净变动'},
        {'name': 'account_count', 'type': 'INT', 'comment': '账户数'},
        {'name': 'holding_product_count', 'type': 'INT', 'comment': '持仓产品数'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'dws_customer_value_profile'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'dws_customer_value_profile',
        '关联条件': '无（单表查询）',
        '过滤条件': 'stat_date = MAX(stat_date)',
        '聚合粒度': 'stat_date + ranking',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_ads_customer_aum_ranking.sql'
    }
)

# ADS: ads_customer_value_level_dist
write_mapping_csv(
    'mapping_ads_customer_value_level_dist.csv',
    {
        '需求名称': '客户资产价值分析体系',
        '需求标识': 'option_a',
        '表名': 'ads_customer_value_level_dist',
        '中文表名': '客户价值等级分布表',
        '层级': 'ADS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'customer_value_level', 'type': 'VARCHAR(30)', 'comment': '客户价值等级', 'pk': True, 'not_null': True},
        {'name': 'level_name', 'type': 'VARCHAR(30)', 'comment': '等级名称', 'calc_logic': "CASE WHEN high_net_worth THEN 高净值客户 WHEN middle THEN 中端客户 ELSE 普通客户 END"},
        {'name': 'customer_count', 'type': 'INT', 'comment': '客户数', 'calc_logic': 'COUNT(*)'},
        {'name': 'total_aum', 'type': 'DECIMAL(18,2)', 'comment': '总AUM', 'calc_logic': 'SUM(total_aum)'},
        {'name': 'avg_aum', 'type': 'DECIMAL(18,2)', 'comment': '平均AUM', 'calc_logic': 'AVG(total_aum)'},
        {'name': 'min_aum', 'type': 'DECIMAL(18,2)', 'comment': '最小AUM', 'calc_logic': 'MIN(total_aum)'},
        {'name': 'max_aum', 'type': 'DECIMAL(18,2)', 'comment': '最大AUM', 'calc_logic': 'MAX(total_aum)'},
        {'name': 'aum_percentage', 'type': 'DECIMAL(8,4)', 'comment': 'AUM占比(%)', 'calc_logic': 'SUM(total_aum) * 100 / 总AUM'},
        {'name': 'customer_percentage', 'type': 'DECIMAL(8,4)', 'comment': '客户占比(%)', 'calc_logic': 'COUNT(*) * 100 / 总客户数'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'dws_customer_value_profile'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'dws_customer_value_profile',
        '关联条件': '无（单表聚合）',
        '过滤条件': 'stat_date = MAX(stat_date)',
        '聚合粒度': 'stat_date + customer_value_level',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_ads_customer_value_level_dist.sql'
    }
)

# ADS: ads_customer_net_asset_change
write_mapping_csv(
    'mapping_ads_customer_net_asset_change.csv',
    {
        '需求名称': '客户资产价值分析体系',
        '需求标识': 'option_a',
        '表名': 'ads_customer_net_asset_change',
        '中文表名': '客户资产净变动指标表',
        '层级': 'ADS',
        '创建日期': '2026-06-10',
        '最后更新': '2026-06-10'
    },
    [
        {'name': 'stat_date', 'type': 'VARCHAR(20)', 'comment': '统计日期', 'pk': True, 'not_null': True},
        {'name': 'customer_id', 'type': 'VARCHAR(50)', 'comment': '客户ID', 'pk': True, 'not_null': True},
        {'name': 'customer_name', 'type': 'VARCHAR(100)', 'comment': '客户姓名', 'calc_logic': "CONCAT(first_name, ' ', last_name)"},
        {'name': 'city', 'type': 'VARCHAR(50)', 'comment': '城市'},
        {'name': 'purchase_amount', 'type': 'DECIMAL(18,2)', 'comment': '申购金额'},
        {'name': 'redemption_amount', 'type': 'DECIMAL(18,2)', 'comment': '赎回金额'},
        {'name': 'profit_loss', 'type': 'DECIMAL(18,2)', 'comment': '盈亏'},
        {'name': 'net_asset_change', 'type': 'DECIMAL(18,2)', 'comment': '资产净变动'},
        {'name': 'change_rate', 'type': 'DECIMAL(8,4)', 'comment': '变动率(%)', 'calc_logic': 'net_asset_change * 100 / holding_market_value'},
        {'name': 'dm_src_info', 'type': 'VARCHAR(100)', 'comment': '数据来源表', 'calc_logic': "'dwd_customer_asset_daily'"},
        {'name': 'etl_load_time', 'type': 'DATETIME', 'comment': 'ETL加载时间', 'calc_logic': 'NOW()'}
    ],
    {
        '数据来源': 'dwd_customer_asset_daily, ods_customer',
        '关联条件': 'dwd.customer_id = ods_customer.customer_id',
        '过滤条件': 'stat_date = MAX(stat_date)',
        '聚合粒度': 'stat_date + customer_id',
        '更新策略': '全量刷新，日频',
        'ETL脚本': 'etl/etl_ads_customer_net_asset_change.sql'
    }
)

print("\n所有选项A Mapping CSV 文件已生成（UTF-8-BOM编码）")
