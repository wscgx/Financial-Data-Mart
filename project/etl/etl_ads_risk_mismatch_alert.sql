-- ETL Script: etl_ads_risk_mismatch_alert.sql
-- 数据来源: dwd_customer_risk_match, ods_customer
-- 目标表: ads_risk_mismatch_alert (风险错配预警清单表)
-- 说明: 生成风险错配预警清单，包含预警类型和级别

INSERT IGNORE INTO ads_risk_mismatch_alert (
    stat_date,
    alert_id,
    customer_id,
    customer_name,
    customer_risk_level,
    product_id,
    product_name,
    product_risk_level,
    risk_gap,
    holding_market_value,
    assessment_valid_until,
    alert_type,
    alert_level,
    alert_message,
    dm_src_info,
    etl_load_time
)
SELECT
    d.stat_date,
    CONCAT('ALERT_', d.stat_date, '_', d.customer_id, '_', d.holding_id) AS alert_id,
    d.customer_id,
    CONCAT(c.last_name, c.first_name) AS customer_name,
    d.customer_risk_level,
    d.product_id,
    d.product_name,
    d.product_risk_level,
    d.risk_gap,
    d.holding_market_value,
    d.assessment_valid_until,
    CASE
        WHEN d.risk_match_flag = 'mismatch' AND d.assessment_valid_until < CURDATE() THEN 'both'
        WHEN d.risk_match_flag = 'mismatch' THEN 'mismatch'
        WHEN d.assessment_valid_until < CURDATE() THEN 'expired'
    END AS alert_type,
    CASE
        WHEN d.risk_gap >= 3 THEN 'high'
        WHEN d.risk_gap >= 2 THEN 'medium'
        ELSE 'low'
    END AS alert_level,
    CONCAT(
        '客户 ', c.last_name, c.first_name,
        ' (风险等级: ', d.customer_risk_level, ')',
        ' 持有产品 ', d.product_name,
        ' (风险等级: ', d.product_risk_level, ')',
        CASE
            WHEN d.risk_match_flag = 'mismatch' AND d.assessment_valid_until < CURDATE()
            THEN '，风险错配且测评已过期'
            WHEN d.risk_match_flag = 'mismatch'
            THEN '，风险错配'
            WHEN d.assessment_valid_until < CURDATE()
            THEN '，测评已过期'
        END
    ) AS alert_message,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM
    dwd_customer_risk_match d
    JOIN ods_customer c ON d.customer_id = c.customer_id AND c.is_current = 1
WHERE
    d.risk_match_flag = 'mismatch'
    OR d.assessment_valid_until < CURDATE();
