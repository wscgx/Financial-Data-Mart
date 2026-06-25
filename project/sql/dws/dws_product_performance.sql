-- DWS Layer: dws_product_performance
-- 产品业绩宽表

CREATE TABLE IF NOT EXISTS dws_product_performance (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品ID',
    product_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品名称',
    product_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品类型',
    risk_level VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '风险等级',
    manager VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '基金经理',
    total_sales_amount DECIMAL(18,2) COMMENT '累计销售金额',
    total_redemption_amount DECIMAL(18,2) COMMENT '累计赎回金额',
    net_sales_amount DECIMAL(18,2) COMMENT '净销售金额',
    total_customer_count INT COMMENT '累计交易客户数',
    avg_daily_sales DECIMAL(18,2) COMMENT '日均销售额',
    weekly_sales_amount DECIMAL(18,2) COMMENT '本周销售额',
    monthly_sales_amount DECIMAL(18,2) COMMENT '本月销售额',
    expected_return DECIMAL(8,4) COMMENT '预期收益率',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品业绩宽表';

CREATE INDEX idx_dws_product_perf_date ON dws_product_performance(stat_date);
CREATE INDEX idx_dws_product_perf_product ON dws_product_performance(product_id);
CREATE INDEX idx_dws_product_perf_type ON dws_product_performance(product_type);