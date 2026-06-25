-- ADS Layer: ads_avg_daily_aum_monthly
-- 日均AUM月指标表

CREATE TABLE IF NOT EXISTS ads_avg_daily_aum_monthly (
    stat_month VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计月份',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    avg_daily_aum DECIMAL(18,2) COMMENT '日均AUM',
    trading_days INT COMMENT '交易天数',
    total_aum_sum DECIMAL(18,2) COMMENT 'AUM总和',
    etl_load_time VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_month, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日均AUM月指标表';

CREATE INDEX idx_ads_avg_aum_month ON ads_avg_daily_aum_monthly(stat_month);
CREATE INDEX idx_ads_avg_aum_customer ON ads_avg_daily_aum_monthly(customer_id);