-- ADS Layer: ads_customer_aum_ranking
-- 客户AUM排名表

CREATE TABLE IF NOT EXISTS ads_customer_aum_ranking (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    ranking INT COMMENT '排名',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    total_aum DECIMAL(18,2) COMMENT '总资产规模',
    customer_value_level VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户价值等级',
    avg_daily_aum_30d DECIMAL(18,2) COMMENT '30日日均AUM',
    total_purchase_amount DECIMAL(18,2) COMMENT '总申购金额',
    total_redemption_amount DECIMAL(18,2) COMMENT '总赎回金额',
    total_profit_loss DECIMAL(18,2) COMMENT '总盈亏',
    net_asset_change DECIMAL(18,2) COMMENT '资产净变动',
    account_count INT COMMENT '账户数',
    holding_product_count INT COMMENT '持仓产品数',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, ranking)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户AUM排名表';

CREATE INDEX idx_ads_customer_aum_date ON ads_customer_aum_ranking(stat_date);
CREATE INDEX idx_ads_customer_aum_customer ON ads_customer_aum_ranking(customer_id);
CREATE INDEX idx_ads_customer_aum_level ON ads_customer_aum_ranking(customer_value_level);