-- ADS Layer: ads_multi_dimension_analysis
-- 多维度交叉分析表

CREATE TABLE IF NOT EXISTS ads_multi_dimension_analysis (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    dimension_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '维度类型(region/product/risk/customer_level)',
    dimension_value VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '维度值',
    customer_count INT COMMENT '客户数',
    aum DECIMAL(18,2) COMMENT 'AUM',
    transaction_amount DECIMAL(18,2) COMMENT '交易额',
    purchase_amount DECIMAL(18,2) COMMENT '申购金额',
    redemption_amount DECIMAL(18,2) COMMENT '赎回金额',
    avg_aum_per_customer DECIMAL(18,2) COMMENT '户均AUM',
    avg_transaction_per_customer DECIMAL(18,2) COMMENT '户均交易额',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, dimension_type, dimension_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多维度交叉分析表';

CREATE INDEX idx_ads_multi_stat_date ON ads_multi_dimension_analysis(stat_date);
CREATE INDEX idx_ads_multi_dimension_type ON ads_multi_dimension_analysis(dimension_type);