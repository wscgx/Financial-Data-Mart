-- ETL Script: etl_ads_risk_metrics_daily.sql
-- 数据来源: dwd_customer_risk_match, dws_risk_compliance_summary, ads_risk_mismatch_alert
-- 目标表: ads_risk_metrics_daily (风险指标日汇总表)
-- 说明: 计算选项C定义的10个风险指标

-- 1. 风险错配客户数 (risk_mismatch_customer_count)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'risk_mismatch_customer_count' AS metric_name,
    COUNT(DISTINCT customer_id) AS metric_value,
    'count' AS metric_type,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_risk_match
WHERE risk_match_flag = 'mismatch'
GROUP BY stat_date;

-- 2. 测评过期率 (assessment_expired_rate)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'assessment_expired_rate' AS metric_name,
    SUM(CASE WHEN is_assessment_expired = 'yes' THEN 1 ELSE 0 END) / COUNT(*) AS metric_value,
    'rate' AS metric_type,
    'dws_risk_compliance_summary' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_risk_compliance_summary
GROUP BY stat_date;

-- 3. 高风险产品持有率 (high_risk_product_holding_rate)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'high_risk_product_holding_rate' AS metric_name,
    COUNT(DISTINCT CASE WHEN product_risk_level IN ('medium_high', 'high') THEN customer_id END) / COUNT(DISTINCT customer_id) AS metric_value,
    'rate' AS metric_type,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_risk_match
GROUP BY stat_date;

-- 4. 风险错配持仓数 (risk_mismatch_holding_count)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'risk_mismatch_holding_count' AS metric_name,
    COUNT(holding_id) AS metric_value,
    'count' AS metric_type,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_risk_match
WHERE risk_match_flag = 'mismatch'
GROUP BY stat_date;

-- 5. 风险错配持仓市值 (risk_mismatch_holding_market_value)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'risk_mismatch_holding_market_value' AS metric_name,
    SUM(holding_market_value) AS metric_value,
    'amount' AS metric_type,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_risk_match
WHERE risk_match_flag = 'mismatch'
GROUP BY stat_date;

-- 6. 合规客户占比 (compliance_customer_rate)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'compliance_customer_rate' AS metric_name,
    SUM(CASE WHEN compliance_status = 'compliant' THEN 1 ELSE 0 END) / COUNT(*) AS metric_value,
    'rate' AS metric_type,
    'dws_risk_compliance_summary' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_risk_compliance_summary
GROUP BY stat_date;

-- 7. 预警客户数 (warning_customer_count)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'warning_customer_count' AS metric_name,
    COUNT(DISTINCT CASE WHEN compliance_status = 'warning' THEN customer_id END) AS metric_value,
    'count' AS metric_type,
    'dws_risk_compliance_summary' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_risk_compliance_summary
GROUP BY stat_date;

-- 8. 违规客户数 (violation_customer_count)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'violation_customer_count' AS metric_name,
    COUNT(DISTINCT CASE WHEN compliance_status = 'violation' THEN customer_id END) AS metric_value,
    'count' AS metric_type,
    'dws_risk_compliance_summary' AS dm_src_info,
    NOW() AS etl_load_time
FROM dws_risk_compliance_summary
GROUP BY stat_date;

-- 9. 平均风险差距 (avg_risk_gap)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'avg_risk_gap' AS metric_name,
    AVG(CASE WHEN risk_match_flag = 'mismatch' THEN risk_gap END) AS metric_value,
    'rate' AS metric_type,
    'dwd_customer_risk_match' AS dm_src_info,
    NOW() AS etl_load_time
FROM dwd_customer_risk_match
GROUP BY stat_date;

-- 10. 高风险预警数 (high_alert_count)
INSERT IGNORE INTO ads_risk_metrics_daily (stat_date, metric_name, metric_value, metric_type, dm_src_info, etl_load_time)
SELECT 
    stat_date,
    'high_alert_count' AS metric_name,
    COUNT(alert_id) AS metric_value,
    'count' AS metric_type,
    'ads_risk_mismatch_alert' AS dm_src_info,
    NOW() AS etl_load_time
FROM ads_risk_mismatch_alert
WHERE alert_level = 'high'
GROUP BY stat_date;
