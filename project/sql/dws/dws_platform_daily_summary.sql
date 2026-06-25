-- DWS Layer: dws_platform_daily_summary
-- 平台日汇总宽表

CREATE TABLE IF NOT EXISTS dws_platform_daily_summary (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    total_customers INT COMMENT '总客户数',
    active_customers INT COMMENT '活跃客户数',
    total_aum DECIMAL(18,2) COMMENT '平台总AUM',
    avg_daily_aum DECIMAL(18,2) COMMENT '日均AUM',
    total_transaction_amount DECIMAL(18,2) COMMENT '总交易额',
    total_purchase_amount DECIMAL(18,2) COMMENT '总申购金额',
    total_redemption_amount DECIMAL(18,2) COMMENT '总赎回金额',
    net_purchase_amount DECIMAL(18,2) COMMENT '净申购金额',
    total_products INT COMMENT '产品总数',
    active_products INT COMMENT '在售产品数',
    holding_customers INT COMMENT '有持仓客户数',
    product_coverage_rate DECIMAL(5,4) COMMENT '产品覆盖率(有持仓客户数/总客户数)',
    new_customers INT COMMENT '新增客户数',
    churn_customers INT COMMENT '流失客户数',
    net_customer_growth INT COMMENT '客户净增数',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台日汇总宽表';

CREATE INDEX idx_dws_platform_stat_date ON dws_platform_daily_summary(stat_date);