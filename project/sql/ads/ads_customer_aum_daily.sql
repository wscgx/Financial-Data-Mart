-- ADS Layer: ads_customer_aum_daily
-- 客户AUM日指标表

CREATE TABLE IF NOT EXISTS ads_customer_aum_daily (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    holding_market_value DECIMAL(18,2) COMMENT '持仓市值',
    cash_balance DECIMAL(18,2) COMMENT '现金余额',
    total_aum DECIMAL(18,2) COMMENT '总资产规模',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户AUM日指标表';

CREATE INDEX idx_ads_aum_date ON ads_customer_aum_daily(stat_date);
CREATE INDEX idx_ads_aum_customer ON ads_customer_aum_daily(customer_id);