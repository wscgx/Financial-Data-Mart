-- ETL: DWD + ODS -> ADS
-- ads_branch_sales_ranking 网点销售排名表

REPLACE INTO ads_branch_sales_ranking (
    stat_date,
    branch,
    total_sales_amount,
    total_redemption_amount,
    net_sales_amount,
    transaction_count,
    customer_count,
    sales_ranking,
    sales_share,
    dm_src_info,
    etl_load_time
)
SELECT
    branch_stats.stat_date,
    branch_stats.branch,
    branch_stats.total_sales_amount,
    branch_stats.total_redemption_amount,
    branch_stats.net_sales_amount,
    branch_stats.transaction_count,
    branch_stats.customer_count,
    RANK() OVER (PARTITION BY branch_stats.stat_date ORDER BY branch_stats.total_sales_amount DESC) AS sales_ranking,
    ROUND(branch_stats.total_sales_amount / NULLIF(SUM(branch_stats.total_sales_amount) OVER (PARTITION BY branch_stats.stat_date), 0), 4) AS sales_share,
    'ods_transaction' AS dm_src_info,
    NOW() AS etl_load_time
FROM (
    SELECT
        t.transaction_date AS stat_date,
        a.branch,
        COALESCE(SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END), 0) AS total_sales_amount,
        COALESCE(SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END), 0) AS total_redemption_amount,
        COALESCE(SUM(CASE WHEN t.transaction_type = 'purchase' THEN t.amount ELSE 0 END), 0) - 
        COALESCE(SUM(CASE WHEN t.transaction_type = 'redemption' THEN t.amount ELSE 0 END), 0) AS net_sales_amount,
        COUNT(t.transaction_id) AS transaction_count,
        COUNT(DISTINCT a.customer_id) AS customer_count
    FROM ods_transaction t
    LEFT JOIN ods_account a ON t.account_id = a.account_id AND a.is_current = 1
    WHERE t.transaction_type IN ('purchase', 'redemption')
      AND t.is_current = 1
    GROUP BY t.transaction_date, a.branch
) branch_stats;
