-- ODS Layer: ods_transaction
-- 交易流水表

CREATE TABLE IF NOT EXISTS ods_transaction (
    transaction_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT '交易ID',
    account_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '账户ID',
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品ID',
    transaction_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '交易类型',
    amount DECIMAL(18,2) COMMENT '交易金额',
    price DECIMAL(18,4) COMMENT '交易价格',
    quantity DECIMAL(18,4) COMMENT '交易数量',
    transaction_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '交易日期',
    fee DECIMAL(18,2) COMMENT '手续费',
    status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '状态',
    start_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '生效日期',
    end_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '失效日期',
    is_current INT COMMENT '是否当前版本',
    etl_load_time VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'ETL加载时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易流水表';

CREATE INDEX idx_ods_transaction_is_current ON ods_transaction(is_current);
CREATE INDEX idx_ods_transaction_account_id ON ods_transaction(account_id);
CREATE INDEX idx_ods_transaction_date ON ods_transaction(transaction_date);
CREATE INDEX idx_ods_transaction_type ON ods_transaction(transaction_type);