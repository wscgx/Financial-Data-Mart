-- ODS Layer: ods_holding
-- 持仓信息表

CREATE TABLE IF NOT EXISTS ods_holding (
    holding_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT '持仓ID',
    account_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '账户ID',
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品ID',
    quantity DECIMAL(18,4) COMMENT '持仓数量',
    avg_cost DECIMAL(18,4) COMMENT '平均成本',
    market_value DECIMAL(18,2) COMMENT '市值',
    profit_loss DECIMAL(18,2) COMMENT '盈亏',
    as_of_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据日期',
    start_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '生效日期',
    end_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '失效日期',
    is_current INT COMMENT '是否当前版本',
    etl_load_time VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'ETL加载时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='持仓信息表';

CREATE INDEX idx_ods_holding_is_current ON ods_holding(is_current);
CREATE INDEX idx_ods_holding_account_id ON ods_holding(account_id);
CREATE INDEX idx_ods_holding_as_of_date ON ods_holding(as_of_date);