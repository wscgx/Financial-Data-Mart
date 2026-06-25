-- ADS Layer: ads_executive_dashboard
-- 高管驾驶舱

CREATE TABLE IF NOT EXISTS ads_executive_dashboard (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    report_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '报告类型(daily/weekly/monthly)',
    total_customers INT COMMENT '总客户数',
    active_customers INT COMMENT '活跃客户数',
    customer_growth_rate DECIMAL(5,4) COMMENT '客户增长率(环比)',
    total_aum DECIMAL(18,2) COMMENT '平台总AUM',
    aum_growth_rate DECIMAL(5,4) COMMENT 'AUM增长率(环比)',
    avg_daily_aum DECIMAL(18,2) COMMENT '日均AUM',
    total_transaction_amount DECIMAL(18,2) COMMENT '总交易额',
    net_purchase_amount DECIMAL(18,2) COMMENT '净申购金额',
    transaction_growth_rate DECIMAL(5,4) COMMENT '交易额增长率(环比)',
    total_products INT COMMENT '产品总数',
    active_products INT COMMENT '在售产品数',
    product_coverage_rate DECIMAL(5,4) COMMENT '产品覆盖率',
    transaction_conversion_rate DECIMAL(5,4) COMMENT '交易转化率(有交易客户数/活跃客户数)',
    new_customers INT COMMENT '新增客户数',
    churn_customers INT COMMENT '流失客户数',
    net_customer_growth INT COMMENT '客户净增数',
    yoy_aum_growth DECIMAL(5,4) COMMENT 'AUM同比增长率',
    yoy_transaction_growth DECIMAL(5,4) COMMENT '交易额同比增长率',
    mom_aum_growth DECIMAL(5,4) COMMENT 'AUM环比增长率',
    mom_transaction_growth DECIMAL(5,4) COMMENT '交易额环比增长率',
    target_achievement_rate DECIMAL(5,4) COMMENT '目标达成率',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='高管驾驶舱';

CREATE INDEX idx_ads_exec_stat_date ON ads_executive_dashboard(stat_date);
CREATE INDEX idx_ads_exec_report_type ON ads_executive_dashboard(report_type);