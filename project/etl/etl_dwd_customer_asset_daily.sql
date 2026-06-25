-- ETL: ODS -> DWD
-- dwd_customer_asset_daily 客户资产日快照表

INSERT IGNORE INTO dwd_customer_asset_daily (
    stat_date,
    customer_id,
    account_id,
    customer_name,
    city,
    branch,
    holding_market_value,
    purchase_amount,
    redemption_amount,
    profit_loss,
    net_asset_change,
    dm_src_info,
    etl_load_time
)
SELECT
    h.as_of_date AS stat_date,
    a.customer_id,
    h.account_id,
    CONCAT(c.last_name, c.first_name) AS customer_name,
    c.city,
    a.branch,
    COALESCE(h.market_value, 0) AS holding_market_value,
    COALESCE(t.purchase_amount, 0) AS purchase_amount,
    COALESCE(t.redemption_amount, 0) AS redemption_amount,
    COALESCE(h.profit_loss, 0) AS profit_loss,
    COALESCE(t.purchase_amount, 0) - COALESCE(t.redemption_amount, 0) + COALESCE(h.profit_loss, 0) AS net_asset_change,
    'ods_holding' AS dm_src_info,
    NOW() AS etl_load_time
FROM ods_holding h
LEFT JOIN ods_account a ON h.account_id = a.account_id AND a.is_current = 1
LEFT JOIN ods_customer c ON a.customer_id = c.customer_id AND c.is_current = 1
LEFT JOIN (
    SELECT
        account_id,
        transaction_date,
        SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END) AS purchase_amount,
        SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END) AS redemption_amount
    FROM ods_transaction
    WHERE transaction_type IN ('purchase', 'redemption')
    GROUP BY account_id, transaction_date
) t ON a.account_id = t.account_id AND h.as_of_date = t.transaction_date
WHERE h.is_current = 1;
