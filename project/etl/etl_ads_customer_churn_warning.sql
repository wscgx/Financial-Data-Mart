-- ETL Script: etl_ads_customer_churn_warning.sql
-- 数据来源: dws_customer_behavior_profile
-- 目标表: ads_customer_churn_warning (客户流失预警表)
-- 说明: 筛选有流失风险的客户，生成预警记录

INSERT IGNORE INTO ads_customer_churn_warning (
    stat_date,
    warning_id,
    customer_id,
    customer_name,
    city,
    branch,
    last_transaction_date,
    days_inactive,
    total_transaction_count,
    total_purchase_amount,
    avg_transaction_amount,
    asset_trend,
    churn_risk_level,
    churn_risk_score,
    warning_reason,
    dm_src_info,
    etl_load_time
)
SELECT
    b.stat_date,
    CONCAT('CHURN_', b.stat_date, '_', b.customer_id) AS warning_id,
    b.customer_id,
    b.customer_name,
    b.city,
    b.branch,
    b.last_transaction_date,
    b.days_inactive,
    b.total_transaction_count,
    b.total_purchase_amount,
    b.avg_transaction_amount,
    b.asset_trend,
    b.churn_risk_level,
    CASE
        WHEN b.churn_risk_level = 'high' AND b.asset_trend = 'decreasing' THEN 90.0
        WHEN b.churn_risk_level = 'high' THEN 80.0
        WHEN b.churn_risk_level = 'medium' AND b.asset_trend = 'decreasing' THEN 70.0
        WHEN b.churn_risk_level = 'medium' THEN 60.0
        WHEN b.churn_risk_level = 'low' AND b.asset_trend = 'decreasing' THEN 50.0
        WHEN b.churn_risk_level = 'low' THEN 40.0
        ELSE 0.0
    END AS churn_risk_score,
    CONCAT(
        '客户 ', b.customer_name,
        ' 已 ', b.days_inactive, ' 天未交易',
        CASE
            WHEN b.asset_trend = 'decreasing' THEN '，且资产持续下降'
            WHEN b.asset_trend = 'increasing' THEN '，但资产呈上升趋势'
            ELSE '，资产保持稳定'
        END
    ) AS warning_reason,
    'dws_customer_behavior_profile' AS dm_src_info,
    NOW() AS etl_load_time
FROM
    dws_customer_behavior_profile b
WHERE
    b.churn_risk_level IN ('high', 'medium', 'low')
    AND b.days_inactive > 0;
