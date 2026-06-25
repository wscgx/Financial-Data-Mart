-- ETL Script: etl_dwd_customer_risk_match.sql
-- 数据来源: ods_holding, ods_product, ods_risk_assessment, ods_account
-- 目标表: dwd_customer_risk_match (客户风险匹配明细表)
-- 说明: 关联持仓、产品、风险测评数据，计算客户风险匹配情况
-- 风险等级映射:
--   产品: low=1, medium_low=2, medium=3, medium_high=4, high=5
--   客户: conservative=1, cautious=2, balanced=3, growth=4, aggressive=5

INSERT IGNORE INTO dwd_customer_risk_match (
    stat_date,
    customer_id,
    account_id,
    holding_id,
    product_id,
    product_name,
    product_risk_level,
    customer_risk_level,
    risk_match_flag,
    risk_gap,
    holding_market_value,
    holding_quantity,
    assessment_date,
    assessment_valid_until,
    assessment_status,
    dm_src_info,
    etl_load_time
)
SELECT
    h.as_of_date AS stat_date,
    a.customer_id,
    h.account_id,
    h.holding_id,
    h.product_id,
    p.product_name,
    p.risk_level AS product_risk_level,
    r.risk_category AS customer_risk_level,
    CASE
        WHEN (CASE p.risk_level
            WHEN 'low' THEN 1
            WHEN 'medium_low' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'medium_high' THEN 4
            WHEN 'high' THEN 5
            ELSE 0
        END) > (CASE r.risk_category
            WHEN 'conservative' THEN 1
            WHEN 'cautious' THEN 2
            WHEN 'balanced' THEN 3
            WHEN 'growth' THEN 4
            WHEN 'aggressive' THEN 5
            ELSE 0
        END) THEN 'mismatch'
        ELSE 'matched'
    END AS risk_match_flag,
    CASE
        WHEN (CASE p.risk_level
            WHEN 'low' THEN 1
            WHEN 'medium_low' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'medium_high' THEN 4
            WHEN 'high' THEN 5
            ELSE 0
        END) > (CASE r.risk_category
            WHEN 'conservative' THEN 1
            WHEN 'cautious' THEN 2
            WHEN 'balanced' THEN 3
            WHEN 'growth' THEN 4
            WHEN 'aggressive' THEN 5
            ELSE 0
        END)
        THEN (CASE p.risk_level
            WHEN 'low' THEN 1
            WHEN 'medium_low' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'medium_high' THEN 4
            WHEN 'high' THEN 5
            ELSE 0
        END) - (CASE r.risk_category
            WHEN 'conservative' THEN 1
            WHEN 'cautious' THEN 2
            WHEN 'balanced' THEN 3
            WHEN 'growth' THEN 4
            WHEN 'aggressive' THEN 5
            ELSE 0
        END)
        ELSE 0
    END AS risk_gap,
    h.market_value AS holding_market_value,
    h.quantity AS holding_quantity,
    r.assessment_date,
    r.valid_until AS assessment_valid_until,
    r.status AS assessment_status,
    'ods_holding' AS dm_src_info,
    NOW() AS etl_load_time
FROM
    ods_holding h
    JOIN ods_account a ON h.account_id = a.account_id AND a.is_current = 1
    JOIN ods_product p ON h.product_id = p.product_id AND p.is_current = 1
    LEFT JOIN ods_risk_assessment r ON a.customer_id = r.customer_id
        AND r.is_current = 1
        AND r.status = 'valid';
