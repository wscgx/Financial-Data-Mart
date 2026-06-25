-- ADS Layer: ads_customer_net_asset_change
-- 客户资产净变动指标表

CREATE TABLE IF NOT EXISTS ads_customer_net_asset_change (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    purchase_amount DECIMAL(18,2) COMMENT '申购金额',
    redemption_amount DECIMAL(18,2) COMMENT '赎回金额',
    profit_loss DECIMAL(18,2) COMMENT '盈亏',
    net_asset_change DECIMAL(18,2) COMMENT '资产净变动',
    change_rate DECIMAL(8,4) COMMENT '变动率(%)',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户资产净变动指标表';

CREATE INDEX idx_ads_net_change_date ON ads_customer_net_asset_change(stat_date);
CREATE INDEX idx_ads_net_change_customer ON ads_customer_net_asset_change(customer_id);