-- DWD Layer: dwd_customer_asset_daily
-- 客户资产日快照表

CREATE TABLE IF NOT EXISTS dwd_customer_asset_daily (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    account_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '账户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    branch VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '网点',
    holding_market_value DECIMAL(18,2) COMMENT '持仓市值',
    purchase_amount DECIMAL(18,2) COMMENT '申购金额',
    redemption_amount DECIMAL(18,2) COMMENT '赎回金额',
    profit_loss DECIMAL(18,2) COMMENT '盈亏',
    net_asset_change DECIMAL(18,2) COMMENT '资产净变动',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id, account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户资产日快照表';

CREATE INDEX idx_dwd_customer_asset_date ON dwd_customer_asset_daily(stat_date);
CREATE INDEX idx_dwd_customer_asset_customer ON dwd_customer_asset_daily(customer_id);