-- ADS Layer: ads_risk_mismatch_alert
-- 风险错配预警清单表

CREATE TABLE IF NOT EXISTS ads_risk_mismatch_alert (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    alert_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '预警ID',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    customer_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户风险等级',
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品ID',
    product_name VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品名称',
    product_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品风险等级',
    risk_gap INT COMMENT '风险等级差距',
    holding_market_value DECIMAL(18,2) COMMENT '持仓市值',
    assessment_valid_until VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评有效期至',
    alert_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '预警类型: mismatch/expired/both',
    alert_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '预警级别: high/medium/low',
    alert_message TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '预警信息',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, alert_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风险错配预警清单表';