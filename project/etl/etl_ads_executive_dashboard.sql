-- ETL: DWS -> ADS
-- ads_executive_dashboard 高管驾驶舱

INSERT IGNORE INTO ads_executive_dashboard (
    stat_date,
    report_type,
    total_customers,
    active_customers,
    customer_growth_rate,
    total_aum,
    aum_growth_rate,
    avg_daily_aum,
    total_transaction_amount,
    net_purchase_amount,
    transaction_growth_rate,
    total_products,
    active_products,
    product_coverage_rate,
    transaction_conversion_rate,
    new_customers,
    churn_customers,
    net_customer_growth,
    yoy_aum_growth,
    yoy_transaction_growth,
    mom_aum_growth,
    mom_transaction_growth,
    target_achievement_rate,
    dm_src_info,
    etl_load_time
)
SELECT 
    s.stat_date,
    'daily' AS report_type,
    s.total_customers,
    s.active_customers,
    CASE WHEN prev.total_customers > 0 
         THEN CAST(s.total_customers - prev.total_customers AS DECIMAL(5,4)) / prev.total_customers 
         ELSE 0 END AS customer_growth_rate,
    s.total_aum,
    CASE WHEN prev.total_aum > 0 
         THEN CAST(s.total_aum - prev.total_aum AS DECIMAL(5,4)) / prev.total_aum 
         ELSE 0 END AS aum_growth_rate,
    s.avg_daily_aum,
    s.total_transaction_amount,
    s.net_purchase_amount,
    CASE WHEN prev.total_transaction_amount > 0 
         THEN CAST(s.total_transaction_amount - prev.total_transaction_amount AS DECIMAL(5,4)) / prev.total_transaction_amount 
         ELSE 0 END AS transaction_growth_rate,
    s.total_products,
    s.active_products,
    s.product_coverage_rate,
    CASE WHEN s.active_customers > 0 
         THEN CAST(COALESCE(tc.transacting_customers, 0) AS DECIMAL(5,4)) / s.active_customers 
         ELSE 0 END AS transaction_conversion_rate,
    s.new_customers,
    s.churn_customers,
    s.net_customer_growth,
    CASE WHEN yoy.total_aum > 0 
         THEN CAST(s.total_aum - yoy.total_aum AS DECIMAL(5,4)) / yoy.total_aum 
         ELSE 0 END AS yoy_aum_growth,
    CASE WHEN yoy.total_transaction_amount > 0 
         THEN CAST(s.total_transaction_amount - yoy.total_transaction_amount AS DECIMAL(5,4)) / yoy.total_transaction_amount 
         ELSE 0 END AS yoy_transaction_growth,
    CASE WHEN mom.total_aum > 0 
         THEN CAST(s.total_aum - mom.total_aum AS DECIMAL(5,4)) / mom.total_aum 
         ELSE 0 END AS mom_aum_growth,
    CASE WHEN mom.total_transaction_amount > 0 
         THEN CAST(s.total_transaction_amount - mom.total_transaction_amount AS DECIMAL(5,4)) / mom.total_transaction_amount 
         ELSE 0 END AS mom_transaction_growth,
    CASE WHEN s.total_aum > 0 
         THEN CAST(s.total_aum AS DECIMAL(5,4)) / (s.total_aum * 1.2) 
         ELSE 0 END AS target_achievement_rate,
    'dws_platform_daily_summary' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_platform_daily_summary s
LEFT JOIN dws_platform_daily_summary prev 
    ON prev.stat_date = DATE_SUB(s.stat_date, INTERVAL 1 DAY)
LEFT JOIN dws_platform_daily_summary mom 
    ON mom.stat_date = DATE_SUB(s.stat_date, INTERVAL 30 DAY)
LEFT JOIN dws_platform_daily_summary yoy 
    ON yoy.stat_date = DATE_SUB(s.stat_date, INTERVAL 365 DAY)
LEFT JOIN (
    SELECT t.transaction_date AS stat_date, COUNT(DISTINCT a.customer_id) AS transacting_customers
    FROM ods_transaction t
    JOIN ods_account a ON t.account_id = a.account_id
    WHERE t.is_current = 1 AND a.is_current = 1
    GROUP BY t.transaction_date
) tc ON s.stat_date = tc.stat_date;
