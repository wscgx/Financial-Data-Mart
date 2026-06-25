-- ETL Script: etl_dwd_customer_activity_daily.sql
-- 数据来源: ods_transaction, ods_account, ods_customer
-- 目标表: dwd_customer_activity_daily (客户活跃度日表)
-- 说明: 按客户+账户+日期统计交易活跃度指标

INSERT IGNORE INTO dwd_customer_activity_daily (
    stat_date,
    customer_id,
    account_id,
    customer_name,
    branch,
    city,
    transaction_count,
    purchase_count,
    redemption_count,
    purchase_amount,
    redemption_amount,
    net_amount,
    total_fee,
    unique_product_count,
    product_types,
    max_single_transaction_amount,
    preferred_product_type,
    last_transaction_date,
    days_since_last_transaction,
    dm_src_info,
    etl_load_time
)
SELECT
    t.transaction_date AS stat_date,
    a.customer_id,
    t.account_id,
    CONCAT(c.last_name, c.first_name) AS customer_name,
    a.branch,
    c.city,
    COUNT(*) AS transaction_count,
    SUM(CASE WHEN t.transaction_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_count,
    SUM(CASE WHEN t.transaction_type = 'redemption' THEN 1 ELSE 0 END) AS redemption_count,
    SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
    SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount,
    SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) - 
    SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS net_amount,
    SUM(t.fee) AS total_fee,
    COUNT(DISTINCT t.product_id) AS unique_product_count,
    GROUP_CONCAT(DISTINCT p.product_type SEPARATOR ',') AS product_types,
    MAX(t.amount) AS max_single_transaction_amount,
    (SELECT p2.product_type
     FROM ods_transaction t2
     JOIN ods_product p2 ON t2.product_id = p2.product_id AND p2.is_current = 1
     WHERE t2.account_id = t.account_id
       AND t2.transaction_date = t.transaction_date
       AND t2.is_current = 1 AND t2.status = 'completed'
     GROUP BY p2.product_type
     ORDER BY COUNT(*) DESC
     LIMIT 1) AS preferred_product_type,
    MAX(t.transaction_date) AS last_transaction_date,
    0 AS days_since_last_transaction,
    'ods_transaction' AS dm_src_info,
    NOW() AS etl_load_time
FROM
    ods_transaction t
    JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
    JOIN ods_customer c ON a.customer_id = c.customer_id AND c.is_current = 1
    LEFT JOIN ods_product p ON t.product_id = p.product_id AND p.is_current = 1
WHERE
    t.is_current = 1
    AND t.status = 'completed'
GROUP BY
    t.transaction_date,
    a.customer_id,
    t.account_id,
    CONCAT(c.last_name, c.first_name),
    a.branch,
    c.city;
