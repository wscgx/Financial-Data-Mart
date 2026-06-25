-- ADS Layer: ads_branch_sales_ranking
-- 网点销售排名表

CREATE TABLE IF NOT EXISTS ads_branch_sales_ranking (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    branch VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '网点名称',
    total_sales_amount DECIMAL(18,2) COMMENT '销售总额',
    total_redemption_amount DECIMAL(18,2) COMMENT '赎回总额',
    net_sales_amount DECIMAL(18,2) COMMENT '净销售额',
    transaction_count INT COMMENT '交易笔数',
    customer_count INT COMMENT '交易客户数',
    sales_ranking INT COMMENT '销售排名',
    sales_share DECIMAL(8,4) COMMENT '销售占比',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, branch)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='网点销售排名表';

CREATE INDEX idx_ads_branch_ranking_date ON ads_branch_sales_ranking(stat_date);
CREATE INDEX idx_ads_branch_ranking_branch ON ads_branch_sales_ranking(branch);