-- ETL: 指标M004 - 资产净变动日指标
-- ads_customer_net_asset_change

INSERT IGNORE INTO ads_customer_net_asset_change (
    stat_date,
    customer_id,
    customer_name,
    city,
    purchase_amount,
    redemption_amount,
    profit_loss,
    net_asset_change,
    change_rate,
    dm_src_info,
    etl_load_time
)
SELECT
    d.stat_date,
    d.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.city,
    d.purchase_amount,
    d.redemption_amount,
    d.profit_loss,
    d.net_asset_change,
    CASE
        WHEN d.holding_market_value > 0 THEN d.net_asset_change * 100.0 / d.holding_market_value
        ELSE 0.0
    END AS change_rate,
    'dwd_customer_asset_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_asset_daily d
LEFT JOIN ods_customer c ON d.customer_id = c.customer_id
WHERE d.stat_date = (SELECT MAX(stat_date) FROM dwd_customer_asset_daily);
