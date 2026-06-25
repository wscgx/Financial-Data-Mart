-- ODS Layer: ods_risk_assessment
-- 客户风险测评表

CREATE TABLE IF NOT EXISTS ods_risk_assessment (
    customer_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '客户ID',
    assessment_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '测评日期',
    risk_category VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '风险等级',
    score DECIMAL(18,2) COMMENT '测评分数',
    questionnaire_version VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '问卷版本',
    valid_until VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '有效期至',
    status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '状态',
    start_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '生效日期',
    end_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '失效日期',
    is_current INT COMMENT '是否当前版本',
    etl_load_time VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'ETL加载时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户风险测评表';

CREATE INDEX idx_ods_risk_customer ON ods_risk_assessment(customer_id);
CREATE INDEX idx_ods_risk_category ON ods_risk_assessment(risk_category);
CREATE INDEX idx_ods_risk_status ON ods_risk_assessment(status);