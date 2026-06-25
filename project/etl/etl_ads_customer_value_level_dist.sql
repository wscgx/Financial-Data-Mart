-- ETL: 指标M002 - 客户价值等级分布
-- ads_customer_value_level_dist

INSERT IGNORE INTO ads_customer_value_level_dist (
    stat_date,
    customer_value_level,
    level_name,
    customer_count,
    total_aum,
    avg_aum,
    min_aum,
    max_aum,
    aum_percentage,
    customer_percentage,
    dm_src_info,
    etl_load_time
)
SELECT
    stat_date,
    customer_value_level,
    CASE customer_value_level
        WHEN 'high_net_worth' THEN '高净值客户'
        WHEN 'middle' THEN '中端客户'
        WHEN 'regular' THEN '普通客户'
    END AS level_name,
    COUNT(*) AS customer_count,
    SUM(total_aum) AS total_aum,
    AVG(total_aum) AS avg_aum,
    MIN(total_aum) AS min_aum,
    MAX(total_aum) AS max_aum,
    SUM(total_aum) * 100.0 / (SELECT SUM(total_aum) FROM dws_customer_value_profile WHERE stat_date = d.stat_date) AS aum_percentage,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dws_customer_value_profile WHERE stat_date = d.stat_date) AS customer_percentage,
    'dws_customer_value_profile' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_customer_value_profile d
WHERE stat_date = (SELECT MAX(stat_date) FROM dws_customer_value_profile)
GROUP BY stat_date, customer_value_level;
