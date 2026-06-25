-- ETL Script: etl_dws_risk_compliance_summary.sql
-- 数据来源: dwd_customer_risk_match, ods_customer
-- 目标表: dws_risk_compliance_summary (合规风险汇总表)
-- 说明: 按客户聚合风险匹配情况，计算合规状态

INSERT IGNORE INTO dws_risk_compliance_summary (
    stat_date,
    customer_id,
    customer_name,
    customer_risk_level,
    assessment_status,
    assessment_valid_until,
    is_assessment_expired,
    total_holding_count,
    mismatch_holding_count,
    mismatch_product_ids,
    total_holding_market_value,
    mismatch_holding_market_value,
    mismatch_ratio,
    max_risk_gap,
    compliance_status,
    dm_src_info,
    etl_load_time
)
SELECT
    d.stat_date,
    d.customer_id,
    CONCAT(c.last_name, c.first_name) AS customer_name,
    d.customer_risk_level,
    d.assessment_status,
    d.assessment_valid_until,
    CASE
        WHEN d.assessment_valid_until < CURDATE() THEN 'yes'
        ELSE 'no'
    END AS is_assessment_expired,
    COUNT(*) AS total_holding_count,
    SUM(CASE WHEN d.risk_match_flag = 'mismatch' THEN 1 ELSE 0 END) AS mismatch_holding_count,
    GROUP_CONCAT(CASE WHEN d.risk_match_flag = 'mismatch' THEN d.product_id END SEPARATOR ',') AS mismatch_product_ids,
    SUM(d.holding_market_value) AS total_holding_market_value,
    SUM(CASE WHEN d.risk_match_flag = 'mismatch' THEN d.holding_market_value ELSE 0 END) AS mismatch_holding_market_value,
    CASE
        WHEN COUNT(*) > 0
        THEN SUM(CASE WHEN d.risk_match_flag = 'mismatch' THEN 1 ELSE 0 END) / COUNT(*)
        ELSE 0
    END AS mismatch_ratio,
    MAX(d.risk_gap) AS max_risk_gap,
    CASE
        WHEN SUM(CASE WHEN d.risk_match_flag = 'mismatch' THEN 1 ELSE 0 END) = 0 THEN 'compliant'
        WHEN MAX(d.risk_gap) <= 1 THEN 'warning'
        ELSE 'violation'
    END AS compliance_status,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM
    dwd_customer_risk_match d
    LEFT JOIN ods_customer c ON d.customer_id = c.customer_id AND c.is_current = 1
GROUP BY
    d.stat_date,
    d.customer_id,
    c.last_name,
    c.first_name,
    d.customer_risk_level,
    d.assessment_status,
    d.assessment_valid_until;
