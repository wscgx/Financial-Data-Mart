-- ETL: 指标M001 - 客户AUM日指标
-- ads_customer_aum_daily

INSERT IGNORE INTO ads_customer_aum_daily (
    stat_date,
    customer_id,
    customer_name,
    city,
    holding_market_value,
    cash_balance,
    total_aum,
    dm_src_info,
    etl_load_time
)
SELECT
    d.stat_date,
    d.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.city,
    d.holding_market_value,
    0.0 AS cash_balance,
    d.holding_market_value AS total_aum,
    'dwd_customer_asset_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_asset_daily d
LEFT JOIN ods_customer c ON d.customer_id = c.customer_id
WHERE d.stat_date = (SELECT MAX(stat_date) FROM dwd_customer_asset_daily);
