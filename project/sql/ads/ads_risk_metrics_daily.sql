-- ADS Layer: ads_risk_metrics_daily
-- 风险指标日汇总表

CREATE TABLE IF NOT EXISTS ads_risk_metrics_daily (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    metric_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '指标名称',
    metric_value DECIMAL(18,4) COMMENT '指标值',
    metric_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '指标类型: count/rate/amount',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, metric_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风险指标日汇总表';