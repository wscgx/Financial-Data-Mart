-- ETL: DWS -> ADS
-- ads_customer_aum_ranking 客户 AUM 排名表

INSERT IGNORE INTO ads_customer_aum_ranking (
    stat_date,
    ranking,
    customer_id,
    customer_name,
    city,
    total_aum,
    customer_value_level,
    avg_daily_aum_30d,
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
    stat_date,
    ROW_NUMBER() OVER (ORDER BY total_aum DESC) AS ranking,
    customer_id,
    CONCAT(first_name, ' ', last_name) AS customer_name,
    city,
    total_aum,
    customer_value_level,
    avg_daily_aum_30d,
    total_purchase_amount,
    total_redemption_amount,
    total_profit_loss,
    net_asset_change,
    account_count,
    holding_product_count,
    'dws_customer_value_profile' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_customer_value_profile
WHERE stat_date = (SELECT MAX(stat_date) FROM dws_customer_value_profile);
