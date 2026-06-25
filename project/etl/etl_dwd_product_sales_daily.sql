-- ETL: ODS -> DWD
-- dwd_product_sales_daily 产品销售日汇总表

REPLACE INTO dwd_product_sales_daily (
    stat_date,
    product_id,
    product_name,
    product_type,
    purchase_amount,
    redemption_amount,
    net_purchase_amount,
    purchase_count,
    redemption_count,
    customer_count,
    total_fee,
    dm_src_info,
    etl_load_time
)
SELECT
    t.transaction_date AS stat_date,
    t.product_id,
    p.product_name,
    p.product_type,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END), 0) AS purchase_amount,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END), 0) AS redemption_amount,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END), 0) AS net_purchase_amount,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'purchase' THEN 1 ELSE 0 END), 0) AS purchase_count,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'redemption' THEN 1 ELSE 0 END), 0) AS redemption_count,
    COUNT(DISTINCT a.customer_id) AS customer_count,
    COALESCE(SUM(t.fee), 0) AS total_fee,
    'ods_transaction' AS dm_src_info,
    NOW() AS etl_load_time
FROM ods_transaction t
LEFT JOIN ods_product p ON t.product_id = p.product_id AND p.is_current = 1
LEFT JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
WHERE t.transaction_type IN ('purchase', 'redemption')
  AND t.is_current = 1
GROUP BY t.transaction_date, t.product_id, p.product_name, p.product_type;
