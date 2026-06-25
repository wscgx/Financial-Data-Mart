-- DWS Layer: dws_customer_behavior_profile
-- 客户行为画像宽表

CREATE TABLE IF NOT EXISTS dws_customer_behavior_profile (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    branch VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '网点',
    total_transaction_count INT COMMENT '总交易笔数',
    total_purchase_amount DECIMAL(18,2) COMMENT '总申购金额',
    total_redemption_amount DECIMAL(18,2) COMMENT '总赎回金额',
    avg_transaction_amount DECIMAL(18,2) COMMENT '平均交易金额',
    max_transaction_amount DECIMAL(18,2) COMMENT '最大单笔交易金额',
    transaction_frequency DECIMAL(10,2) COMMENT '交易频率(笔/月)',
    preferred_product_type VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '偏好产品类型',
    preferred_transaction_hour INT COMMENT '偏好交易时段',
    large_transaction_count INT COMMENT '大额交易笔数',
    large_transaction_amount DECIMAL(18,2) COMMENT '大额交易总额',
    last_transaction_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '最后交易日期',
    days_inactive INT COMMENT '未交易天数',
    churn_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '流失风险等级',
    asset_trend VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '资产趋势',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户行为画像宽表';