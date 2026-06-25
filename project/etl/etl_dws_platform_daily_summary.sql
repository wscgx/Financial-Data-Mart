-- ETL: DWD -> DWS
-- dws_platform_daily_summary 平台日汇总宽表
-- 优化: 交易汇总数据改用 dwd_customer_activity_daily，不再直接访问 ods_transaction

INSERT IGNORE INTO dws_platform_daily_summary (
    stat_date,
    total_customers,
    active_customers,
    total_aum,
    avg_daily_aum,
    total_transaction_amount,
    total_purchase_amount,
    total_redemption_amount,
    net_purchase_amount,
    total_products,
    active_products,
    holding_customers,
    product_coverage_rate,
    new_customers,
    churn_customers,
    net_customer_growth,
    dm_src_info,
    etl_load_time
)
SELECT
    t.stat_date,
    t.total_customers,
    t.active_customers,
    COALESCE(a.total_aum, 0) AS total_aum,
    COALESCE(a.avg_daily_aum, 0) AS avg_daily_aum,
    COALESCE(tx.total_transaction_amount, 0) AS total_transaction_amount,
    COALESCE(tx.total_purchase_amount, 0) AS total_purchase_amount,
    COALESCE(tx.total_redemption_amount, 0) AS total_redemption_amount,
    COALESCE(tx.total_purchase_amount, 0) - COALESCE(tx.total_redemption_amount, 0) AS net_purchase_amount,
    COALESCE(p.total_products, 0) AS total_products,
    COALESCE(p.active_products, 0) AS active_products,
    COALESCE(h.holding_customers, 0) AS holding_customers,
    CASE WHEN t.total_customers > 0 
         THEN CAST(COALESCE(h.holding_customers, 0) AS DECIMAL(5,4)) / t.total_customers 
         ELSE 0 END AS product_coverage_rate,
    COALESCE(c.new_customers, 0) AS new_customers,
    COALESCE(c.churn_customers, 0) AS churn_customers,
    COALESCE(c.new_customers, 0) - COALESCE(c.churn_customers, 0) AS net_customer_growth,
    'dwd_customer_asset_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT 
        stat_date,
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT CASE WHEN holding_market_value > 0 THEN customer_id END) AS active_customers
    FROM dwd_customer_asset_daily
    GROUP BY stat_date
) t
LEFT JOIN (
    SELECT 
        stat_date,
        SUM(holding_market_value) AS total_aum,
        AVG(holding_market_value) AS avg_daily_aum
    FROM dwd_customer_asset_daily
    GROUP BY stat_date
) a ON t.stat_date = a.stat_date
LEFT JOIN (
    SELECT 
        stat_date,
        SUM(purchase_amount + redemption_amount) AS total_transaction_amount,
        SUM(purchase_amount) AS total_purchase_amount,
        SUM(redemption_amount) AS total_redemption_amount
    FROM dwd_customer_activity_daily
    GROUP BY stat_date
) tx ON t.stat_date = tx.stat_date
LEFT JOIN (
    SELECT 
        CURDATE() AS stat_date,
        COUNT(*) AS total_products,
        COUNT(CASE WHEN status = 'active' THEN 1 END) AS active_products
    FROM ods_product
    WHERE is_current = 1
) p ON t.stat_date = p.stat_date
LEFT JOIN (
    SELECT 
        stat_date,
        COUNT(DISTINCT customer_id) AS holding_customers
    FROM dwd_customer_asset_daily
    WHERE holding_market_value > 0
    GROUP BY stat_date
) h ON t.stat_date = h.stat_date
LEFT JOIN (
    SELECT 
        stat_date,
        COUNT(CASE WHEN is_new = 1 THEN customer_id END) AS new_customers,
        COUNT(CASE WHEN is_churn = 1 THEN customer_id END) AS churn_customers
    FROM (
        SELECT 
            customer_id,
            stat_date,
            CASE WHEN rn = 1 THEN 1 ELSE 0 END AS is_new,
            CASE WHEN days_since_last > 90 THEN 1 ELSE 0 END AS is_churn
        FROM (
            SELECT 
                customer_id,
                stat_date,
                ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY stat_date ASC) AS rn,
                DATEDIFF(stat_date, LAG(stat_date) OVER (PARTITION BY customer_id ORDER BY stat_date ASC)) AS days_since_last
            FROM dwd_customer_asset_daily
        ) sub
    ) sub2
    GROUP BY stat_date
) c ON t.stat_date = c.stat_date;
