-- Data Quality Validation Rules
-- 客户资产价值分析体系 - 数据质量校验

-- 1. DWD层校验: 检查AUM是否为负数
SELECT
    'dwd_negative_aum' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_asset_daily
WHERE holding_market_value < 0;

-- 2. DWD层校验: 检查日期是否合理
SELECT
    'dwd_invalid_date' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_asset_daily
WHERE stat_date > CURDATE() OR stat_date IS NULL;

-- 3. DWD层校验: 检查客户ID是否为空
SELECT
    'dwd_null_customer_id' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_asset_daily
WHERE customer_id IS NULL OR customer_id = '';

-- 4. DWS层校验: 检查客户价值等级是否合理
SELECT
    'dws_invalid_value_level' AS check_name,
    COUNT(*) AS failed_records
FROM dws_customer_value_profile
WHERE customer_value_level NOT IN ('high_net_worth', 'middle', 'regular');

-- 5. DWS层校验: 检查AUM计算是否正确
SELECT
    'dws_aum_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM dws_customer_value_profile
WHERE ABS(total_aum - daily_aum) > 0.01;

-- 6. ADS层校验: 检查排名是否连续
SELECT
    'ads_ranking_gap' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        ranking,
        LEAD(ranking) OVER (ORDER BY ranking) AS next_ranking
    FROM ads_customer_aum_ranking
    WHERE stat_date = (SELECT MAX(stat_date) FROM ads_customer_aum_ranking)
)
WHERE next_ranking - ranking > 1;

-- 7. 跨层校验: DWD汇总与DWS对比
SELECT
    'dwd_dws_aum_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        dwd.stat_date,
        dwd.customer_id,
        dwd.total_aum AS dwd_aum,
        dws.total_aum AS dws_aum
    FROM (
        SELECT stat_date, customer_id, SUM(holding_market_value) AS total_aum
        FROM dwd_customer_asset_daily
        GROUP BY stat_date, customer_id
    ) dwd
    LEFT JOIN dws_customer_value_profile dws
        ON dwd.stat_date = dws.stat_date AND dwd.customer_id = dws.customer_id
    WHERE ABS(dwd.total_aum - dws.total_aum) > 0.01
);

-- 8. 完整性校验: 检查是否有客户缺失AUM数据
SELECT
    'missing_customer_aum' AS check_name,
    COUNT(*) AS failed_records
FROM ods_customer c
LEFT JOIN dws_customer_value_profile dws
    ON c.customer_id = dws.customer_id
    AND dws.stat_date = (SELECT MAX(stat_date) FROM dws_customer_value_profile)
WHERE c.is_current = 1
  AND dws.customer_id IS NULL;

-- =====================================================
-- 产品销售与业绩分析 - 数据质量校验 (选项B)
-- =====================================================

-- 9. DWD层校验: 检查产品销售金额是否为负数
SELECT
    'dwd_negative_sales_amount' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_product_sales_daily
WHERE purchase_amount < 0 OR redemption_amount < 0;

-- 10. DWD层校验: 检查产品ID是否为空
SELECT
    'dwd_null_product_id' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_product_sales_daily
WHERE product_id IS NULL OR product_id = '';

-- 11. DWD层校验: 检查净申购金额计算是否正确
SELECT
    'dwd_net_purchase_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_product_sales_daily
WHERE ABS(net_purchase_amount - (purchase_amount - redemption_amount)) > 0.01;

-- 12. DWS层校验: 检查累计销售额是否递减
SELECT
    'dws_decreasing_total_sales' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        product_id,
        stat_date,
        total_sales_amount,
        LAG(total_sales_amount) OVER (PARTITION BY product_id ORDER BY stat_date) AS prev_total_sales
    FROM dws_product_performance
)
WHERE prev_total_sales IS NOT NULL AND total_sales_amount < prev_total_sales - 0.01;

-- 13. ADS层校验: 检查销售占比总和是否接近1
SELECT
    'ads_sales_share_sum_invalid' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        stat_date,
        SUM(sales_share) AS total_share
    FROM ads_branch_sales_ranking
    GROUP BY stat_date
    HAVING ABS(total_share - 1.0) > 0.01
);

-- 14. ADS层校验: 检查排名是否连续
SELECT
    'ads_branch_ranking_gap' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        stat_date,
        branch,
        sales_ranking,
        LEAD(sales_ranking) OVER (PARTITION BY stat_date ORDER BY sales_ranking) AS next_ranking
    FROM ads_branch_sales_ranking
)
WHERE next_ranking IS NOT NULL AND next_ranking - sales_ranking > 1;

-- =====================================================
-- 综合财富管理驾驶舱 - 数据质量校验 (选项E)
-- =====================================================

-- 16. DWS层校验: 检查平台总AUM是否为负数
SELECT
    'dws_total_aum_negative' AS check_name,
    COUNT(*) AS failed_records
FROM dws_platform_daily_summary
WHERE total_aum < 0;

-- 17. DWS层校验: 检查客户数是否合理（总客户数应≥活跃客户数）
SELECT
    'dws_customer_count_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM dws_platform_daily_summary
WHERE total_customers < active_customers;

-- 18. DWS层校验: 检查产品覆盖率是否在0-1之间
SELECT
    'dws_coverage_rate_range' AS check_name,
    COUNT(*) AS failed_records
FROM dws_platform_daily_summary
WHERE product_coverage_rate < 0 OR product_coverage_rate > 1;

-- 19. ADS层校验: 检查增长率是否在合理范围内(-1~10)
SELECT
    'ads_growth_rate_range' AS check_name,
    COUNT(*) AS failed_records
FROM ads_executive_dashboard
WHERE aum_growth_rate < -1 OR aum_growth_rate > 10
   OR transaction_growth_rate < -1 OR transaction_growth_rate > 10;

-- 20. ADS层校验: 检查转化率是否在0-1之间
SELECT
    'ads_conversion_rate_range' AS check_name,
    COUNT(*) AS failed_records
FROM ads_executive_dashboard
WHERE transaction_conversion_rate < 0 OR transaction_conversion_rate > 1;

-- 21. ADS层校验: 检查多维度AUM一致性（各维度AUM总和应与平台总AUM一致）
SELECT
    'multi_aum_consistency' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        m.stat_date,
        SUM(m.aum) AS dimension_aum_sum,
        d.total_aum AS platform_aum
    FROM ads_multi_dimension_analysis m
    JOIN dws_platform_daily_summary d ON m.stat_date = d.stat_date
    WHERE m.dimension_type = 'region'
    GROUP BY m.stat_date, d.total_aum
    HAVING ABS(dimension_aum_sum - platform_aum) / platform_aum > 0.05
);

-- 22. ADS层校验: 检查异常级别是否有效
SELECT
    'anomaly_level_valid' AS check_name,
    COUNT(*) AS failed_records
FROM ads_anomaly_detection
WHERE anomaly_level NOT IN ('low', 'medium', 'high');

-- 23. ADS层校验: 检查异常偏差率计算是否正确
SELECT
    'anomaly_deviation_calc' AS check_name,
    COUNT(*) AS failed_records
FROM ads_anomaly_detection
WHERE expected_value > 0 
  AND ABS(deviation_rate - (current_value - expected_value) / expected_value) > 0.0001;

-- 24. 跨层校验: DWS汇总与ODS对比
SELECT
    'dws_ods_customer_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        dws.stat_date,
        dws.total_customers AS dws_customers,
        ods.total_customers AS ods_customers
    FROM dws_platform_daily_summary dws
    JOIN (
        SELECT stat_date, COUNT(DISTINCT customer_id) AS total_customers
        FROM dwd_customer_asset_daily
        GROUP BY stat_date
    ) ods ON dws.stat_date = ods.stat_date
    WHERE dws.total_customers != ods.total_customers
);

-- =====================================================
-- 客户风险匹配度分析 - 数据质量校验 (选项C)
-- =====================================================

-- 25. DWD层校验: 检查风险匹配标志是否有效
SELECT
    'dwd_invalid_risk_match_flag' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_risk_match
WHERE risk_match_flag NOT IN ('matched', 'mismatch');

-- 26. DWD层校验: 检查风险差距是否非负
SELECT
    'dwd_negative_risk_gap' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_risk_match
WHERE risk_gap < 0;

-- 27. DWD层校验: 检查风险等级是否有效
SELECT
    'dwd_invalid_risk_level' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_risk_match
WHERE product_risk_level NOT IN ('conservative', 'cautious', 'balanced', 'growth', 'aggressive')
   OR customer_risk_level NOT IN ('conservative', 'cautious', 'balanced', 'growth', 'aggressive');

-- 28. DWS层校验: 检查合规状态是否有效
SELECT
    'dws_invalid_compliance_status' AS check_name,
    COUNT(*) AS failed_records
FROM dws_risk_compliance_summary
WHERE compliance_status NOT IN ('compliant', 'warning', 'violation');

-- 29. DWS层校验: 检查错配比例是否在0-1之间
SELECT
    'dws_mismatch_ratio_range' AS check_name,
    COUNT(*) AS failed_records
FROM dws_risk_compliance_summary
WHERE mismatch_ratio < 0 OR mismatch_ratio > 1;

-- 30. DWS层校验: 检查持仓数量一致性
SELECT
    'dws_holding_count_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM dws_risk_compliance_summary
WHERE total_holding_count < mismatch_holding_count;

-- 31. ADS层校验: 检查预警级别是否有效
SELECT
    'ads_invalid_alert_level' AS check_name,
    COUNT(*) AS failed_records
FROM ads_risk_mismatch_alert
WHERE alert_level NOT IN ('low', 'medium', 'high');

-- 32. ADS层校验: 检查预警类型是否有效
SELECT
    'ads_invalid_alert_type' AS check_name,
    COUNT(*) AS failed_records
FROM ads_risk_mismatch_alert
WHERE alert_type NOT IN ('mismatch', 'expired', 'both');

-- 33. 跨层校验: DWD汇总与DWS错配持仓数对比
SELECT
    'dwd_dws_mismatch_count_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        dwd.stat_date,
        dwd.customer_id,
        dwd.mismatch_count AS dwd_mismatch_count,
        dws.mismatch_holding_count AS dws_mismatch_count
    FROM (
        SELECT stat_date, customer_id, COUNT(*) AS mismatch_count
        FROM dwd_customer_risk_match
        WHERE risk_match_flag = 'mismatch'
        GROUP BY stat_date, customer_id
    ) dwd
    LEFT JOIN dws_risk_compliance_summary dws
        ON dwd.stat_date = dws.stat_date AND dwd.customer_id = dws.customer_id
    WHERE dwd.mismatch_count != dws.mismatch_holding_count
);

-- 34. 完整性校验: 检查是否有持仓客户缺失风险匹配数据
SELECT
    'missing_risk_match_data' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT DISTINCT customer_id, as_of_date
    FROM ods_holding
    WHERE is_current = 1
) h
LEFT JOIN dwd_customer_risk_match d
    ON h.customer_id = d.customer_id AND h.as_of_date = d.stat_date
WHERE d.customer_id IS NULL;

-- =====================================================
-- 客户交易行为分析 - 数据质量校验 (选项D)
-- =====================================================

-- 35. DWD层校验: 检查交易金额是否为负数
SELECT
    'dwd_negative_amount' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_activity_daily
WHERE purchase_amount < 0 OR redemption_amount < 0;

-- 36. DWD层校验: 检查客户ID是否为空
SELECT
    'dwd_null_customer_id' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_activity_daily
WHERE customer_id IS NULL OR customer_id = '';

-- 37. DWD层校验: 检查统计日期是否合理
SELECT
    'dwd_invalid_date' AS check_name,
    COUNT(*) AS failed_records
FROM dwd_customer_activity_daily
WHERE stat_date > CURDATE() OR stat_date IS NULL;

-- 38. DWS层校验: 检查交易频率是否非负
SELECT
    'dws_negative_frequency' AS check_name,
    COUNT(*) AS failed_records
FROM dws_customer_behavior_profile
WHERE transaction_frequency < 0;

-- 39. DWS层校验: 检查流失风险等级是否有效
SELECT
    'dws_invalid_churn_level' AS check_name,
    COUNT(*) AS failed_records
FROM dws_customer_behavior_profile
WHERE churn_risk_level NOT IN ('high', 'medium', 'low', 'none');

-- 40. DWS层校验: 检查资产趋势是否有效
SELECT
    'dws_invalid_asset_trend' AS check_name,
    COUNT(*) AS failed_records
FROM dws_customer_behavior_profile
WHERE asset_trend NOT IN ('increasing', 'decreasing', 'stable');

-- 41. ADS层校验: 检查风险评分是否非负
SELECT
    'ads_negative_risk_score' AS check_name,
    COUNT(*) AS failed_records
FROM ads_customer_churn_warning
WHERE churn_risk_score < 0;

-- 42. ADS层校验: 检查流失风险等级是否有效
SELECT
    'ads_invalid_churn_level' AS check_name,
    COUNT(*) AS failed_records
FROM ads_customer_churn_warning
WHERE churn_risk_level NOT IN ('high', 'medium', 'low');

-- 43. 跨层校验: DWD汇总与DWS交易笔数对比
SELECT
    'dwd_dws_transaction_mismatch' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT
        dwd.stat_date,
        dwd.customer_id,
        dwd.total_txn_count AS dwd_txn_count,
        dws.total_transaction_count AS dws_txn_count
    FROM (
        SELECT stat_date, customer_id, SUM(transaction_count) AS total_txn_count
        FROM dwd_customer_activity_daily
        GROUP BY stat_date, customer_id
    ) dwd
    LEFT JOIN dws_customer_behavior_profile dws
        ON dwd.stat_date COLLATE utf8mb4_unicode_ci = dws.stat_date COLLATE utf8mb4_unicode_ci
        AND dwd.customer_id COLLATE utf8mb4_unicode_ci = dws.customer_id COLLATE utf8mb4_unicode_ci
    WHERE dwd.total_txn_count != dws.total_transaction_count
);

-- 44. 完整性校验: 检查有交易的客户是否都有活跃度数据
SELECT
    'missing_active_customer' AS check_name,
    COUNT(*) AS failed_records
FROM (
    SELECT DISTINCT a.customer_id, t.transaction_date
    FROM ods_transaction t
    JOIN ods_account a ON t.account_id = a.account_id
    WHERE t.is_current = 1 AND t.status = 'completed' AND a.is_current = 1
) t
LEFT JOIN dwd_customer_activity_daily d
    ON t.customer_id COLLATE utf8mb4_unicode_ci = d.customer_id COLLATE utf8mb4_unicode_ci
    AND t.transaction_date COLLATE utf8mb4_unicode_ci = d.stat_date COLLATE utf8mb4_unicode_ci
WHERE d.customer_id IS NULL;
