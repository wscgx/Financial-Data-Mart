-- ADS Layer: ads_customer_churn_warning
-- 客户流失预警表

CREATE TABLE IF NOT EXISTS ads_customer_churn_warning (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    warning_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '预警ID',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '城市',
    branch VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '网点',
    last_transaction_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '最后交易日期',
    days_inactive INT COMMENT '未交易天数',
    total_transaction_count INT COMMENT '历史交易笔数',
    total_purchase_amount DECIMAL(18,2) COMMENT '历史申购总额',
    avg_transaction_amount DECIMAL(18,2) COMMENT '平均交易金额',
    asset_trend VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '资产趋势',
    churn_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '流失风险等级',
    churn_risk_score DECIMAL(5,2) COMMENT '流失风险评分',
    warning_reason TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '预警原因',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, warning_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户流失预警表';