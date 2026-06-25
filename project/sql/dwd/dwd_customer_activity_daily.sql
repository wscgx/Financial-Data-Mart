-- DWD Layer: dwd_customer_activity_daily
-- 客户活跃度日表

CREATE TABLE IF NOT EXISTS dwd_customer_activity_daily (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    account_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '账户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    branch VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '网点',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    transaction_count INT COMMENT '交易笔数',
    purchase_count INT COMMENT '申购笔数',
    redemption_count INT COMMENT '赎回笔数',
    purchase_amount DECIMAL(18,2) COMMENT '申购金额',
    redemption_amount DECIMAL(18,2) COMMENT '赎回金额',
    net_amount DECIMAL(18,2) COMMENT '净交易金额',
    total_fee DECIMAL(18,2) COMMENT '总手续费',
    unique_product_count INT COMMENT '交易产品数',
    product_types TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '交易产品类型列表',
    max_single_transaction_amount DECIMAL(18,2) COMMENT '最大单笔交易金额',
    preferred_product_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '偏好产品类型',
    last_transaction_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '最后交易日期',
    days_since_last_transaction INT COMMENT '距最后交易天数',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id, account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户活跃度日表';