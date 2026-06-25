-- ETL: DWD -> DWS
-- dws_customer_value_profile 客户价值画像宽表
-- 简化版本，提高性能

INSERT IGNORE INTO dws_customer_value_profile (
    stat_date,
    customer_id,
    first_name,
    last_name,
    city,
    total_aum,
    customer_value_level,
    daily_aum,
    avg_daily_aum_30d,
    avg_daily_aum_90d,
    aum_change_30d,
    total_purchase_amount,
    total_redemption_amount,
    total_profit_loss,
    net_asset_change,
    account_count,
    holding_product_count,
    dm_src_info,
    etl_load_time
)
SELECT
    d.stat_date,
    d.customer_id,
    c.first_name,
    c.last_name,
    c.city,
    d.total_aum,
    CASE
        WHEN d.total_aum >= 1000000 THEN 'high_net_worth'
        WHEN d.total_aum >= 100000 THEN 'middle'
        ELSE 'regular'
    END AS customer_value_level,
    d.daily_aum,
    d.avg_daily_aum_30d,
    d.avg_daily_aum_90d,
    d.aum_change_30d,
    d.total_purchase_amount,
    d.total_redemption_amount,
    d.total_profit_loss,
    d.net_asset_change,
    d.account_count,
    d.holding_product_count,
    'dwd_customer_asset_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT
        stat_date,
        customer_id,
        SUM(holding_market_value) AS total_aum,
        SUM(holding_market_value) AS daily_aum,
        AVG(SUM(holding_market_value)) OVER (
            PARTITION BY customer_id 
            ORDER BY stat_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_daily_aum_30d,
        AVG(SUM(holding_market_value)) OVER (
            PARTITION BY customer_id 
            ORDER BY stat_date 
            ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) AS avg_daily_aum_90d,
        SUM(holding_market_value) - LAG(SUM(holding_market_value), 30) OVER (
            PARTITION BY customer_id 
            ORDER BY stat_date
        ) AS aum_change_30d,
        SUM(purchase_amount) AS total_purchase_amount,
        SUM(redemption_amount) AS total_redemption_amount,
        SUM(profit_loss) AS total_profit_loss,
        SUM(net_asset_change) AS net_asset_change,
        COUNT(DISTINCT account_id) AS account_count,
        COUNT(*) AS holding_product_count
    FROM dwd_customer_asset_daily
    GROUP BY stat_date, customer_id
) d
LEFT JOIN ods_customer c ON d.customer_id = c.customer_id AND c.is_current = 1;
