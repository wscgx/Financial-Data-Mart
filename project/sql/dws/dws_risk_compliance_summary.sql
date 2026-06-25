-- DWS Layer: dws_risk_compliance_summary
-- 合规风险汇总表

CREATE TABLE IF NOT EXISTS dws_risk_compliance_summary (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    customer_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户姓名',
    customer_risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户风险等级',
    assessment_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评状态',
    assessment_valid_until VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评有效期至',
    is_assessment_expired VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评是否过期',
    total_holding_count INT COMMENT '总持仓产品数',
    mismatch_holding_count INT COMMENT '风险错配持仓数',
    mismatch_product_ids TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '错配产品ID列表',
    total_holding_market_value DECIMAL(18,2) COMMENT '总持仓市值',
    mismatch_holding_market_value DECIMAL(18,2) COMMENT '错配持仓市值',
    mismatch_ratio DECIMAL(5,4) COMMENT '错配比例',
    max_risk_gap INT COMMENT '最大风险等级差距',
    compliance_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '合规状态: compliant/warning/violation',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合规风险汇总表';