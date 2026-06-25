-- ODS Layer: ods_product
-- 理财产品表

CREATE TABLE IF NOT EXISTS ods_product (
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT '产品ID',
    product_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品名称',
    product_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品类型',
    risk_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '风险等级',
    min_investment DECIMAL(18,2) COMMENT '最低投资额',
    expected_return DECIMAL(18,4) COMMENT '预期收益率',
    launch_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '发行日期',
    maturity_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '到期日期',
    status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '状态',
    manager VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '基金经理',
    start_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '生效日期',
    end_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '失效日期',
    is_current INT COMMENT '是否当前版本',
    etl_load_time VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'ETL加载时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='理财产品表';

CREATE INDEX idx_ods_product_is_current ON ods_product(is_current);
CREATE INDEX idx_ods_product_type ON ods_product(product_type);
CREATE INDEX idx_ods_product_risk ON ods_product(risk_level);