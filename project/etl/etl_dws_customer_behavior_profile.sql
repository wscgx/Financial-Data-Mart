-- ETL Script: etl_dws_customer_behavior_profile.sql
-- 数据来源: dwd_customer_activity_daily, ods_customer
-- 目标表: dws_customer_behavior_profile (客户行为画像宽表)
-- 说明: 按客户聚合交易行为，计算偏好、频率、流失风险等指标
-- 优化: 所有事实数据均来自 DWD 层，不再直接访问 ODS 事实表

INSERT IGNORE INTO dws_customer_behavior_profile (
    stat_date,
    customer_id,
    customer_name,
    city,
    branch,
    total_transaction_count,
    total_purchase_amount,
    total_redemption_amount,
    avg_transaction_amount,
    max_transaction_amount,
    transaction_frequency,
    preferred_product_type,
    preferred_transaction_hour,
    large_transaction_count,
    large_transaction_amount,
    last_transaction_date,
    days_inactive,
    churn_risk_level,
    asset_trend,
    dm_src_info,
    etl_load_time
)
SELECT
    agg.stat_date,
    agg.customer_id,
    CONCAT(c.last_name, c.first_name) AS customer_name,
    agg.city,
    agg.branch,
    agg.total_transaction_count,
    agg.total_purchase_amount,
    agg.total_redemption_amount,
    agg.avg_transaction_amount,
    agg.max_transaction_amount,
    agg.transaction_frequency,
    agg.preferred_product_type,
    10 AS preferred_transaction_hour,
    agg.large_transaction_count,
    agg.large_transaction_amount,
    agg.last_transaction_date,
    DATEDIFF(agg.stat_date, agg.last_transaction_date) AS days_inactive,
    CASE
        WHEN DATEDIFF(agg.stat_date, agg.last_transaction_date) > 7 THEN 'high'
        WHEN DATEDIFF(agg.stat_date, agg.last_transaction_date) > 3 THEN 'medium'
        WHEN DATEDIFF(agg.stat_date, agg.last_transaction_date) > 1 THEN 'low'
        ELSE 'none'
    END AS churn_risk_level,
    agg.asset_trend,
    'dwd_customer_activity_daily' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT
        (SELECT MAX(stat_date) FROM dwd_customer_activity_daily) AS stat_date,
        d.customer_id,
        MAX(d.city) AS city,
        MAX(d.branch) AS branch,
        SUM(d.transaction_count) AS total_transaction_count,
        SUM(d.purchase_amount) AS total_purchase_amount,
        SUM(d.redemption_amount) AS total_redemption_amount,
        AVG(d.net_amount / NULLIF(d.transaction_count, 0)) AS avg_transaction_amount,
        MAX(d.max_single_transaction_amount) AS max_transaction_amount,
        SUM(d.transaction_count) / GREATEST(DATEDIFF((SELECT MAX(stat_date) FROM dwd_customer_activity_daily), MIN(d.stat_date)), 1) * 30 AS transaction_frequency,
        SUBSTRING_INDEX(
            GROUP_CONCAT(d.preferred_product_type ORDER BY d.transaction_count DESC SEPARATOR ','),
            ',', 1
        ) AS preferred_product_type,
        SUM(CASE WHEN d.purchase_amount > 50000 THEN d.transaction_count ELSE 0 END) AS large_transaction_count,
        SUM(CASE WHEN d.purchase_amount > 50000 THEN d.purchase_amount ELSE 0 END) AS large_transaction_amount,
        MAX(d.last_transaction_date) AS last_transaction_date,
        CASE
            WHEN SUM(d.net_amount) < 0 THEN 'decreasing'
            WHEN SUM(d.net_amount) > 0 THEN 'increasing'
            ELSE 'stable'
        END AS asset_trend
    FROM
        dwd_customer_activity_daily d
    GROUP BY
        d.customer_id
) agg
JOIN ods_customer c ON agg.customer_id = c.customer_id AND c.is_current = 1;
