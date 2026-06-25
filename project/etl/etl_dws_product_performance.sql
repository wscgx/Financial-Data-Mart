-- ETL: DWD -> DWS
-- dws_product_performance 产品业绩宽表

REPLACE INTO dws_product_performance (
    stat_date,
    product_id,
    product_name,
    product_type,
    risk_level,
    manager,
    total_sales_amount,
    total_redemption_amount,
    net_sales_amount,
    total_customer_count,
    avg_daily_sales,
    weekly_sales_amount,
    monthly_sales_amount,
    expected_return,
    dm_src_info,
    etl_load_time
)
SELECT
    dwd.stat_date,
    dwd.product_id,
    dwd.product_name,
    dwd.product_type,
    p.risk_level,
    p.manager,
    COALESCE(SUM(dwd.purchase_amount) OVER (PARTITION BY dwd.product_id ORDER BY dwd.stat_date), 0) AS total_sales_amount,
    COALESCE(SUM(dwd.redemption_amount) OVER (PARTITION BY dwd.product_id ORDER BY dwd.stat_date), 0) AS total_redemption_amount,
    COALESCE(SUM(dwd.net_purchase_amount) OVER (PARTITION BY dwd.product_id ORDER BY dwd.stat_date), 0) AS net_sales_amount,
    COALESCE(SUM(dwd.customer_count) OVER (PARTITION BY dwd.product_id ORDER BY dwd.stat_date), 0) AS total_customer_count,
    COALESCE(AVG(dwd.purchase_amount) OVER (PARTITION BY dwd.product_id ORDER BY dwd.stat_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 0) AS avg_daily_sales,
    COALESCE(SUM(dwd.purchase_amount) OVER (
        PARTITION BY dwd.product_id 
        ORDER BY dwd.stat_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) AS weekly_sales_amount,
    COALESCE(SUM(dwd.purchase_amount) OVER (
        PARTITION BY dwd.product_id 
        ORDER BY dwd.stat_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 0) AS monthly_sales_amount,
    p.expected_return,
    'dwd_product_sales_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_product_sales_daily dwd
LEFT JOIN ods_product p ON dwd.product_id = p.product_id AND p.is_current = 1
WHERE dwd.stat_date IS NOT NULL;
