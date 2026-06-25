-- DWS Layer: dws_customer_value_profile
-- 客户价值画像宽表

CREATE TABLE IF NOT EXISTS dws_customer_value_profile (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    first_name VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '名',
    last_name VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '姓',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    total_aum DECIMAL(18,2) COMMENT '总资产规模',
    customer_value_level VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户价值等级',
    daily_aum DECIMAL(18,2) COMMENT '当日AUM',
    avg_daily_aum_30d DECIMAL(18,2) COMMENT '30日日均AUM',
    avg_daily_aum_90d DECIMAL(18,2) COMMENT '90日日均AUM',
    aum_change_30d DECIMAL(18,2) COMMENT '30日AUM变动',
    total_purchase_amount DECIMAL(18,2) COMMENT '总申购金额',
    total_redemption_amount DECIMAL(18,2) COMMENT '总赎回金额',
    total_profit_loss DECIMAL(18,2) COMMENT '总盈亏',
    net_asset_change DECIMAL(18,2) COMMENT '资产净变动',
    account_count INT COMMENT '账户数',
    holding_product_count INT COMMENT '持仓产品数',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户价值画像宽表';

CREATE INDEX idx_dws_customer_value_date ON dws_customer_value_profile(stat_date);
CREATE INDEX idx_dws_customer_value_customer ON dws_customer_value_profile(customer_id);
CREATE INDEX idx_dws_customer_value_level ON dws_customer_value_profile(customer_value_level);