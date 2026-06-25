-- ADS Layer: ads_customer_value_level_dist
-- 客户价值等级分布表

CREATE TABLE IF NOT EXISTS ads_customer_value_level_dist (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_value_level VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户价值等级',
    level_name VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '等级名称',
    customer_count INT COMMENT '客户数',
    total_aum DECIMAL(18,2) COMMENT '总AUM',
    avg_aum DECIMAL(18,2) COMMENT '平均AUM',
    min_aum DECIMAL(18,2) COMMENT '最小AUM',
    max_aum DECIMAL(18,2) COMMENT '最大AUM',
    aum_percentage DECIMAL(8,4) COMMENT 'AUM占比(%)',
    customer_percentage DECIMAL(8,4) COMMENT '客户占比(%)',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_value_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户价值等级分布表';

CREATE INDEX idx_ads_value_level_date ON ads_customer_value_level_dist(stat_date);