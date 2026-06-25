-- ADS Layer: ads_anomaly_detection
-- 异常检测预警表

CREATE TABLE IF NOT EXISTS ads_anomaly_detection (
    stat_date VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '统计日期',
    anomaly_type VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '异常类型(aum_fluctuation/transaction_anomaly/churn_anomaly)',
    anomaly_level VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '异常级别(low/medium/high)',
    description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '异常描述',
    current_value DECIMAL(18,2) COMMENT '当前值',
    expected_value DECIMAL(18,2) COMMENT '预期值',
    deviation_rate DECIMAL(5,4) COMMENT '偏差率',
    affected_customers INT COMMENT '受影响客户数',
    affected_amount DECIMAL(18,2) COMMENT '受影响金额',
    dm_src_info VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, anomaly_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异常检测预警表';

CREATE INDEX idx_ads_anomaly_stat_date ON ads_anomaly_detection(stat_date);
CREATE INDEX idx_ads_anomaly_type ON ads_anomaly_detection(anomaly_type);