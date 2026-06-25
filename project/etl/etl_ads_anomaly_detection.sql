-- ETL: DWS -> ADS
-- ads_anomaly_detection 异常检测预警表

-- 异常1：AUM异常波动
INSERT IGNORE INTO ads_anomaly_detection (
    stat_date,
    anomaly_type,
    anomaly_level,
    description,
    current_value,
    expected_value,
    deviation_rate,
    affected_customers,
    affected_amount,
    dm_src_info,
    etl_load_time
)
SELECT 
    s.stat_date,
    'aum_fluctuation' AS anomaly_type,
    CASE 
        WHEN ABS(s.deviation_rate) > 0.2 THEN 'high'
        WHEN ABS(s.deviation_rate) > 0.1 THEN 'medium'
        ELSE 'low'
    END AS anomaly_level,
    CONCAT('AUM异常波动：当前值', s.total_aum, '，预期值', s.avg_aum, '，偏差率', s.deviation_rate) AS description,
    s.total_aum AS current_value,
    s.avg_aum AS expected_value,
    s.deviation_rate,
    s.total_customers AS affected_customers,
    s.total_aum AS affected_amount,
    'dws_platform_daily_summary' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT 
        cur.stat_date,
        cur.total_aum,
        cur.total_customers,
        avg_stats.avg_aum,
        CASE WHEN avg_stats.avg_aum > 0 
             THEN CAST(cur.total_aum - avg_stats.avg_aum AS DECIMAL(5,4)) / avg_stats.avg_aum 
             ELSE 0 END AS deviation_rate
    FROM dws_platform_daily_summary cur
    CROSS JOIN (
        SELECT AVG(total_aum) AS avg_aum
        FROM dws_platform_daily_summary
    ) avg_stats
    WHERE cur.stat_date = (SELECT MAX(stat_date) FROM dws_platform_daily_summary)
) s
WHERE ABS(s.deviation_rate) > 0.05;

-- 异常2：交易量异常
INSERT IGNORE INTO ads_anomaly_detection (
    stat_date,
    anomaly_type,
    anomaly_level,
    description,
    current_value,
    expected_value,
    deviation_rate,
    affected_customers,
    affected_amount,
    dm_src_info,
    etl_load_time
)
SELECT 
    t.stat_date,
    'transaction_anomaly' AS anomaly_type,
    CASE 
        WHEN ABS(t.deviation_rate) > 0.3 THEN 'high'
        WHEN ABS(t.deviation_rate) > 0.15 THEN 'medium'
        ELSE 'low'
    END AS anomaly_level,
    CONCAT('交易量异常：当前值', t.total_transaction_amount, '，预期值', t.avg_amount, '，偏差率', t.deviation_rate) AS description,
    t.total_transaction_amount AS current_value,
    t.avg_amount AS expected_value,
    t.deviation_rate,
    t.transaction_customers AS affected_customers,
    t.total_transaction_amount AS affected_amount,
    'ods_transaction' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT 
        cur.stat_date,
        cur.total_transaction_amount,
        cur.transaction_customers,
        avg_stats.avg_amount,
        CASE WHEN avg_stats.avg_amount > 0 
             THEN CAST(cur.total_transaction_amount - avg_stats.avg_amount AS DECIMAL(5,4)) / avg_stats.avg_amount 
             ELSE 0 END AS deviation_rate
    FROM (
        SELECT 
            transaction_date AS stat_date,
            SUM(amount) AS total_transaction_amount,
            COUNT(DISTINCT account_id) AS transaction_customers
        FROM ods_transaction
        WHERE is_current = 1 AND transaction_date = (SELECT MAX(transaction_date) FROM ods_transaction WHERE is_current = 1)
        GROUP BY transaction_date
    ) cur
    CROSS JOIN (
        SELECT AVG(daily_amount) AS avg_amount
        FROM (
            SELECT SUM(amount) AS daily_amount
            FROM ods_transaction
            WHERE is_current = 1
            GROUP BY transaction_date
        ) daily
    ) avg_stats
) t
WHERE ABS(t.deviation_rate) > 0.1;

-- 异常3：客户流失异常
INSERT IGNORE INTO ads_anomaly_detection (
    stat_date,
    anomaly_type,
    anomaly_level,
    description,
    current_value,
    expected_value,
    deviation_rate,
    affected_customers,
    affected_amount,
    dm_src_info,
    etl_load_time
)
SELECT 
    c.stat_date,
    'churn_anomaly' AS anomaly_type,
    CASE 
        WHEN c.churn_rate > 0.05 THEN 'high'
        WHEN c.churn_rate > 0.03 THEN 'medium'
        ELSE 'low'
    END AS anomaly_level,
    CONCAT('客户流失异常：流失率', c.churn_rate, '，流失客户数', c.churn_customers) AS description,
    c.churn_customers AS current_value,
    c.avg_churn_customers AS expected_value,
    CASE WHEN c.avg_churn_customers > 0 
         THEN CAST(c.churn_customers - c.avg_churn_customers AS DECIMAL(5,4)) / c.avg_churn_customers 
         ELSE 0 END AS deviation_rate,
    c.churn_customers AS affected_customers,
    c.churn_aum AS affected_amount,
    'dwd_customer_asset_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT 
        latest_date.stat_date,
        latest_data.churn_customers,
        latest_data.churn_aum,
        latest_data.churn_rate,
        avg_stats.avg_churn_customers
    FROM (
        SELECT MAX(stat_date) AS stat_date
        FROM dwd_customer_asset_daily
    ) latest_date
    JOIN (
        SELECT 
            stat_date,
            COUNT(DISTINCT customer_id) AS churn_customers,
            SUM(holding_market_value) AS churn_aum,
            CAST(COUNT(DISTINCT customer_id) AS DECIMAL(5,4)) / 
                (SELECT COUNT(DISTINCT customer_id) FROM dwd_customer_asset_daily WHERE stat_date = (SELECT MAX(stat_date) FROM dwd_customer_asset_daily)) AS churn_rate
        FROM dwd_customer_asset_daily
        WHERE stat_date = (SELECT MAX(stat_date) FROM dwd_customer_asset_daily)
        GROUP BY stat_date
    ) latest_data ON latest_date.stat_date = latest_data.stat_date
    CROSS JOIN (
        SELECT AVG(churn_customers) AS avg_churn_customers
        FROM (
            SELECT stat_date, COUNT(DISTINCT customer_id) AS churn_customers
            FROM dwd_customer_asset_daily
            GROUP BY stat_date
        ) daily_churn
    ) avg_stats
) c
WHERE c.churn_rate > 0.02;
