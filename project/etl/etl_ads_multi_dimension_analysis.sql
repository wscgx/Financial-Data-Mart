-- ETL: ODS/DWD -> ADS
-- ads_multi_dimension_analysis 多维度交叉分析表

-- 维度1：城市维度
INSERT IGNORE INTO ads_multi_dimension_analysis (
    stat_date,
    dimension_type,
    dimension_value,
    customer_count,
    aum,
    transaction_amount,
    purchase_amount,
    redemption_amount,
    avg_aum_per_customer,
    avg_transaction_per_customer,
    dm_src_info,
    etl_load_time
)
SELECT 
    d.stat_date,
    'region' AS dimension_type,
    COALESCE(c.city, '未知') AS dimension_value,
    COUNT(DISTINCT d.customer_id) AS customer_count,
    SUM(d.holding_market_value) AS aum,
    COALESCE(SUM(t.transaction_amount), 0) AS transaction_amount,
    COALESCE(SUM(t.purchase_amount), 0) AS purchase_amount,
    COALESCE(SUM(t.redemption_amount), 0) AS redemption_amount,
    SUM(d.holding_market_value) / COUNT(DISTINCT d.customer_id) AS avg_aum_per_customer,
    COALESCE(SUM(t.transaction_amount), 0) / COUNT(DISTINCT d.customer_id) AS avg_transaction_per_customer,
    'ods_customer' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_asset_daily d
LEFT JOIN ods_customer c ON d.customer_id = c.customer_id AND c.is_current = 1
LEFT JOIN (
    SELECT 
        a.customer_id,
        t.transaction_date AS stat_date,
        SUM(t.amount) AS transaction_amount,
        SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
        SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount
    FROM ods_transaction t
    JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
    WHERE t.is_current = 1
    GROUP BY a.customer_id, t.transaction_date
) t ON d.customer_id = t.customer_id AND d.stat_date = t.stat_date
WHERE d.stat_date IS NOT NULL
GROUP BY d.stat_date, COALESCE(c.city, '未知');

-- 维度2：产品类型维度
INSERT IGNORE INTO ads_multi_dimension_analysis (
    stat_date,
    dimension_type,
    dimension_value,
    customer_count,
    aum,
    transaction_amount,
    purchase_amount,
    redemption_amount,
    avg_aum_per_customer,
    avg_transaction_per_customer,
    dm_src_info,
    etl_load_time
)
SELECT 
    t.transaction_date AS stat_date,
    'product' AS dimension_type,
    COALESCE(p.product_type, '未知') AS dimension_value,
    COUNT(DISTINCT a.customer_id) AS customer_count,
    COALESCE(SUM(h.market_value), 0) AS aum,
    SUM(t.amount) AS transaction_amount,
    SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
    SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount,
    CASE WHEN COUNT(DISTINCT a.customer_id) > 0 
         THEN COALESCE(SUM(h.market_value), 0) / COUNT(DISTINCT a.customer_id) 
         ELSE 0 END AS avg_aum_per_customer,
    SUM(t.amount) / COUNT(DISTINCT a.customer_id) AS avg_transaction_per_customer,
    'ods_product' AS dm_src_info,
    NOW() AS etl_load_time
FROM ods_transaction t
JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
JOIN ods_product p ON t.product_id = p.product_id AND p.is_current = 1
LEFT JOIN ods_holding h ON a.customer_id = h.account_id 
    AND t.product_id = h.product_id AND h.is_current = 1
WHERE t.is_current = 1
GROUP BY t.transaction_date, COALESCE(p.product_type, '未知');

-- 维度3：风险等级维度
INSERT IGNORE INTO ads_multi_dimension_analysis (
    stat_date,
    dimension_type,
    dimension_value,
    customer_count,
    aum,
    transaction_amount,
    purchase_amount,
    redemption_amount,
    avg_aum_per_customer,
    avg_transaction_per_customer,
    dm_src_info,
    etl_load_time
)
SELECT 
    d.stat_date,
    'risk' AS dimension_type,
    COALESCE(r.risk_category, '未测评') AS dimension_value,
    COUNT(DISTINCT d.customer_id) AS customer_count,
    SUM(d.holding_market_value) AS aum,
    COALESCE(SUM(t.transaction_amount), 0) AS transaction_amount,
    COALESCE(SUM(t.purchase_amount), 0) AS purchase_amount,
    COALESCE(SUM(t.redemption_amount), 0) AS redemption_amount,
    SUM(d.holding_market_value) / COUNT(DISTINCT d.customer_id) AS avg_aum_per_customer,
    COALESCE(SUM(t.transaction_amount), 0) / COUNT(DISTINCT d.customer_id) AS avg_transaction_per_customer,
    'ods_risk_assessment' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_asset_daily d
LEFT JOIN ods_risk_assessment r ON d.customer_id = r.customer_id AND r.is_current = 1
LEFT JOIN (
    SELECT 
        a.customer_id,
        t.transaction_date AS stat_date,
        SUM(t.amount) AS transaction_amount,
        SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
        SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount
    FROM ods_transaction t
    JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
    WHERE t.is_current = 1
    GROUP BY a.customer_id, t.transaction_date
) t ON d.customer_id = t.customer_id AND d.stat_date = t.stat_date
WHERE d.stat_date IS NOT NULL
GROUP BY d.stat_date, COALESCE(r.risk_category, '未测评');

-- 维度4：客户等级维度
INSERT IGNORE INTO ads_multi_dimension_analysis (
    stat_date,
    dimension_type,
    dimension_value,
    customer_count,
    aum,
    transaction_amount,
    purchase_amount,
    redemption_amount,
    avg_aum_per_customer,
    avg_transaction_per_customer,
    dm_src_info,
    etl_load_time
)
SELECT 
    d.stat_date,
    'customer_level' AS dimension_type,
    CASE 
        WHEN d.holding_market_value >= 1000000 THEN '高净值'
        WHEN d.holding_market_value >= 100000 THEN '中端'
        ELSE '普通'
    END AS dimension_value,
    COUNT(DISTINCT d.customer_id) AS customer_count,
    SUM(d.holding_market_value) AS aum,
    COALESCE(SUM(t.transaction_amount), 0) AS transaction_amount,
    COALESCE(SUM(t.purchase_amount), 0) AS purchase_amount,
    COALESCE(SUM(t.redemption_amount), 0) AS redemption_amount,
    SUM(d.holding_market_value) / COUNT(DISTINCT d.customer_id) AS avg_aum_per_customer,
    COALESCE(SUM(t.transaction_amount), 0) / COUNT(DISTINCT d.customer_id) AS avg_transaction_per_customer,
    'dwd_customer_asset_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_asset_daily d
LEFT JOIN (
    SELECT 
        a.customer_id,
        t.transaction_date AS stat_date,
        SUM(t.amount) AS transaction_amount,
        SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END) AS purchase_amount,
        SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END) AS redemption_amount
    FROM ods_transaction t
    JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
    WHERE t.is_current = 1
    GROUP BY a.customer_id, t.transaction_date
) t ON d.customer_id = t.customer_id AND d.stat_date = t.stat_date
WHERE d.stat_date IS NOT NULL
GROUP BY d.stat_date, 
    CASE 
        WHEN d.holding_market_value >= 1000000 THEN '高净值'
        WHEN d.holding_market_value >= 100000 THEN '中端'
        ELSE '普通'
    END;
