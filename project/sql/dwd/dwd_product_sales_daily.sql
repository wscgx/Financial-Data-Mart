-- DWD Layer: dwd_product_sales_daily
-- 产品销售日汇总表

CREATE TABLE IF NOT EXISTS dwd_product_sales_daily (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    product_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品ID',
    product_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品名称',
    product_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品类型',
    purchase_amount DECIMAL(18,2) COMMENT '申购金额',
    redemption_amount DECIMAL(18,2) COMMENT '赎回金额',
    net_purchase_amount DECIMAL(18,2) COMMENT '净申购金额',
    purchase_count INT COMMENT '申购笔数',
    redemption_count INT COMMENT '赎回笔数',
    customer_count INT COMMENT '交易客户数',
    total_fee DECIMAL(18,2) COMMENT '总手续费',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品销售日汇总表';

CREATE INDEX idx_dwd_product_sales_date ON dwd_product_sales_daily(stat_date);
CREATE INDEX idx_dwd_product_sales_product ON dwd_product_sales_daily(product_id);