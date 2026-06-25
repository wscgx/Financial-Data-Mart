-- ETL: 指标M003 - 日均AUM月指标
-- ads_avg_daily_aum_monthly

REPLACE INTO ads_avg_daily_aum_monthly (
    stat_month,
    customer_id,
    customer_name,
    city,
    avg_daily_aum,
    trading_days,
    total_aum_sum,
    etl_load_time
)
SELECT
    DATE_FORMAT(d.stat_date, '%Y-%m') AS stat_month,
    d.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.city,
    SUM(d.holding_market_value) / COUNT(DISTINCT d.stat_date) AS avg_daily_aum,
    COUNT(DISTINCT d.stat_date) AS trading_days,
    SUM(d.holding_market_value) AS total_aum_sum,
    NOW() AS etl_load_time
FROM dwd_customer_asset_daily d
LEFT JOIN ods_customer c ON d.customer_id = c.customer_id
GROUP BY DATE_FORMAT(d.stat_date, '%Y-%m'), d.customer_id, c.first_name, c.last_name, c.city;
