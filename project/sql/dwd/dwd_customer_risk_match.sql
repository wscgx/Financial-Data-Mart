-- DWD Layer: dwd_customer_risk_match
-- 客户风险匹配明细表

CREATE TABLE IF NOT EXISTS dwd_customer_risk_match (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    account_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '账户ID',
    holding_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '持仓ID',
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品ID',
    product_name VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品名称',
    product_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品风险等级',
    customer_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户风险等级',
    risk_match_flag VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '风险匹配标志: matched/mismatch',
    risk_gap INT COMMENT '风险等级差距',
    holding_market_value DECIMAL(18,2) COMMENT '持仓市值',
    holding_quantity DECIMAL(18,4) COMMENT '持仓数量',
    assessment_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '风险测评日期',
    assessment_valid_until VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评有效期至',
    assessment_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评状态',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id, holding_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户风险匹配明细表';