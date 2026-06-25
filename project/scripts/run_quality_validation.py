"""
数据质量校验脚本
执行所有校验规则并生成报告
"""
import pymysql
import csv
import os
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Config
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASS = '123456'
MYSQL_DB = 'financial_dw'

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
REPORT_DIR = os.path.join(BASE_DIR, 'data', 'quality_reports')
os.makedirs(REPORT_DIR, exist_ok=True)


def run_quality_checks(conn):
    """执行所有数据质量校验"""
    cursor = conn.cursor()
    
    # Define all checks as (name, sql) tuples
    checks = [
        # DWD层校验
        ("dwd_negative_aum", """
            SELECT COUNT(*) FROM dwd_customer_asset_daily
            WHERE holding_market_value < 0
        """),
        ("dwd_invalid_date", """
            SELECT COUNT(*) FROM dwd_customer_asset_daily
            WHERE stat_date > CURDATE() OR stat_date IS NULL
        """),
        ("dwd_null_customer_id", """
            SELECT COUNT(*) FROM dwd_customer_asset_daily
            WHERE customer_id IS NULL OR customer_id = ''
        """),
        
        # DWS层校验
        ("dws_invalid_value_level", """
            SELECT COUNT(*) FROM dws_customer_value_profile
            WHERE customer_value_level NOT IN ('high_net_worth', 'middle', 'regular')
        """),
        ("dws_aum_mismatch", """
            SELECT COUNT(*) FROM dws_customer_value_profile
            WHERE ABS(total_aum - daily_aum) > 0.01
        """),
        
        # ADS层校验
        ("ads_ranking_gap", """
            SELECT COUNT(*) FROM (
                SELECT ranking, LEAD(ranking) OVER (ORDER BY ranking) AS next_ranking
                FROM ads_customer_aum_ranking
                WHERE stat_date = (SELECT MAX(stat_date) FROM ads_customer_aum_ranking)
            ) t WHERE next_ranking - ranking > 1
        """),
        
        # 跨层校验
        ("dwd_dws_aum_mismatch", """
            SELECT COUNT(*) FROM (
                SELECT dwd.stat_date, dwd.customer_id, dwd.total_aum AS dwd_aum, dws.total_aum AS dws_aum
                FROM (
                    SELECT stat_date, customer_id, SUM(holding_market_value) AS total_aum
                    FROM dwd_customer_asset_daily
                    GROUP BY stat_date, customer_id
                ) dwd
                LEFT JOIN dws_customer_value_profile dws
                    ON dwd.stat_date = dws.stat_date AND dwd.customer_id = dws.customer_id
                WHERE ABS(dwd.total_aum - dws.total_aum) > 0.01
            ) t
        """),
        ("missing_customer_aum", """
            SELECT COUNT(*) FROM ods_customer c
            LEFT JOIN dws_customer_value_profile dws
                ON c.customer_id = dws.customer_id
                AND dws.stat_date = (SELECT MAX(stat_date) FROM dws_customer_value_profile)
            WHERE c.is_current = 1 AND dws.customer_id IS NULL
        """),
        
        # 产品销售校验
        ("dwd_negative_sales_amount", """
            SELECT COUNT(*) FROM dwd_product_sales_daily
            WHERE purchase_amount < 0 OR redemption_amount < 0
        """),
        ("dwd_null_product_id", """
            SELECT COUNT(*) FROM dwd_product_sales_daily
            WHERE product_id IS NULL OR product_id = ''
        """),
        ("dwd_net_purchase_mismatch", """
            SELECT COUNT(*) FROM dwd_product_sales_daily
            WHERE ABS(net_purchase_amount - (purchase_amount - redemption_amount)) > 0.01
        """),
        ("dws_decreasing_total_sales", """
            SELECT COUNT(*) FROM (
                SELECT product_id, stat_date, total_sales_amount,
                    LAG(total_sales_amount) OVER (PARTITION BY product_id ORDER BY stat_date) AS prev_total_sales
                FROM dws_product_performance
            ) t WHERE prev_total_sales IS NOT NULL AND total_sales_amount < prev_total_sales - 0.01
        """),
        ("ads_sales_share_sum_invalid", """
            SELECT COUNT(*) FROM (
                SELECT stat_date, SUM(sales_share) AS total_share
                FROM ads_branch_sales_ranking
                GROUP BY stat_date
                HAVING ABS(total_share - 1.0) > 0.01
            ) t
        """),
        ("ads_branch_ranking_gap", """
            SELECT COUNT(*) FROM (
                SELECT stat_date, branch, sales_ranking,
                    LEAD(sales_ranking) OVER (PARTITION BY stat_date ORDER BY sales_ranking) AS next_ranking
                FROM ads_branch_sales_ranking
            ) t WHERE next_ranking IS NOT NULL AND next_ranking - sales_ranking > 1
        """),
        
        # 平台汇总校验
        ("dws_total_aum_negative", """
            SELECT COUNT(*) FROM dws_platform_daily_summary WHERE total_aum < 0
        """),
        ("dws_customer_count_mismatch", """
            SELECT COUNT(*) FROM dws_platform_daily_summary WHERE total_customers < active_customers
        """),
        ("dws_coverage_rate_range", """
            SELECT COUNT(*) FROM dws_platform_daily_summary
            WHERE product_coverage_rate < 0 OR product_coverage_rate > 1
        """),
        ("ads_growth_rate_range", """
            SELECT COUNT(*) FROM ads_executive_dashboard
            WHERE aum_growth_rate < -1 OR aum_growth_rate > 10
               OR transaction_growth_rate < -1 OR transaction_growth_rate > 10
        """),
        ("ads_conversion_rate_range", """
            SELECT COUNT(*) FROM ads_executive_dashboard
            WHERE transaction_conversion_rate < 0 OR transaction_conversion_rate > 1
        """),
        ("multi_aum_consistency", """
            SELECT COUNT(*) FROM (
                SELECT m.stat_date, SUM(m.aum) AS dimension_aum_sum, d.total_aum AS platform_aum
                FROM ads_multi_dimension_analysis m
                JOIN dws_platform_daily_summary d ON m.stat_date = d.stat_date
                WHERE m.dimension_type = 'region'
                GROUP BY m.stat_date, d.total_aum
                HAVING ABS(dimension_aum_sum - platform_aum) / platform_aum > 0.05
            ) t
        """),
        ("anomaly_level_valid", """
            SELECT COUNT(*) FROM ads_anomaly_detection
            WHERE anomaly_level NOT IN ('low', 'medium', 'high')
        """),
        ("anomaly_deviation_calc", """
            SELECT COUNT(*) FROM ads_anomaly_detection
            WHERE expected_value > 0
              AND ABS(deviation_rate - (current_value - expected_value) / expected_value) > 0.0001
        """),
        ("dws_ods_customer_mismatch", """
            SELECT COUNT(*) FROM (
                SELECT dws.stat_date, dws.total_customers AS dws_customers, ods.total_customers AS ods_customers
                FROM dws_platform_daily_summary dws
                JOIN (
                    SELECT stat_date, COUNT(DISTINCT customer_id) AS total_customers
                    FROM dwd_customer_asset_daily
                    GROUP BY stat_date
                ) ods ON dws.stat_date = ods.stat_date
                WHERE dws.total_customers != ods.total_customers
            ) t
        """),
        
        # 风险匹配校验
        ("dwd_invalid_risk_match_flag", """
            SELECT COUNT(*) FROM dwd_customer_risk_match
            WHERE risk_match_flag NOT IN ('matched', 'mismatch')
        """),
        ("dwd_negative_risk_gap", """
            SELECT COUNT(*) FROM dwd_customer_risk_match WHERE risk_gap < 0
        """),
        ("dwd_invalid_risk_level", """
            SELECT COUNT(*) FROM dwd_customer_risk_match
            WHERE product_risk_level NOT IN ('low', 'medium_low', 'medium', 'medium_high', 'high')
               OR customer_risk_level NOT IN ('conservative', 'cautious', 'balanced', 'growth', 'aggressive')
        """),
        ("dws_invalid_compliance_status", """
            SELECT COUNT(*) FROM dws_risk_compliance_summary
            WHERE compliance_status NOT IN ('compliant', 'warning', 'violation')
        """),
        ("dws_mismatch_ratio_range", """
            SELECT COUNT(*) FROM dws_risk_compliance_summary
            WHERE mismatch_ratio < 0 OR mismatch_ratio > 1
        """),
        ("dws_holding_count_mismatch", """
            SELECT COUNT(*) FROM dws_risk_compliance_summary
            WHERE total_holding_count < mismatch_holding_count
        """),
        ("ads_invalid_alert_level", """
            SELECT COUNT(*) FROM ads_risk_mismatch_alert
            WHERE alert_level NOT IN ('low', 'medium', 'high')
        """),
        ("ads_invalid_alert_type", """
            SELECT COUNT(*) FROM ads_risk_mismatch_alert
            WHERE alert_type NOT IN ('mismatch', 'expired', 'both')
        """),
        ("dwd_dws_mismatch_count_mismatch", """
            SELECT COUNT(*) FROM (
                SELECT dwd.stat_date, dwd.customer_id, dwd.mismatch_count AS dwd_mismatch_count,
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
            ) t
        """),
        ("missing_risk_match_data", """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT customer_id, as_of_date
                FROM ods_holding WHERE is_current = 1
            ) h
            LEFT JOIN dwd_customer_risk_match d
                ON h.customer_id = d.customer_id AND h.as_of_date = d.stat_date
            WHERE d.customer_id IS NULL
        """),
        
        # 交易行为校验
        ("dwd_negative_amount", """
            SELECT COUNT(*) FROM dwd_customer_activity_daily
            WHERE purchase_amount < 0 OR redemption_amount < 0
        """),
        ("dws_negative_frequency", """
            SELECT COUNT(*) FROM dws_customer_behavior_profile
            WHERE transaction_frequency < 0
        """),
        ("dws_invalid_churn_level", """
            SELECT COUNT(*) FROM dws_customer_behavior_profile
            WHERE churn_risk_level NOT IN ('high', 'medium', 'low', 'none')
        """),
        ("dws_invalid_asset_trend", """
            SELECT COUNT(*) FROM dws_customer_behavior_profile
            WHERE asset_trend NOT IN ('increasing', 'decreasing', 'stable')
        """),
        ("ads_negative_risk_score", """
            SELECT COUNT(*) FROM ads_customer_churn_warning WHERE churn_risk_score < 0
        """),
        ("ads_invalid_churn_level", """
            SELECT COUNT(*) FROM ads_customer_churn_warning
            WHERE churn_risk_level NOT IN ('high', 'medium', 'low')
        """),
    ]
    
    results = []
    for check_name, sql in checks:
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
            failed_records = row[0] if row else 0
            
            status = 'PASS' if failed_records == 0 else 'FAIL'
            results.append({
                'check_name': check_name,
                'failed_records': failed_records,
                'status': status,
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            icon = '✓' if status == 'PASS' else '✗'
            print(f"  {icon} {check_name}: {failed_records} 条异常记录")
            
        except Exception as e:
            results.append({
                'check_name': check_name,
                'failed_records': -1,
                'status': 'ERROR',
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            print(f"  ⚠ {check_name}: 执行错误")
    
    return results


def generate_report(results):
    """生成校验报告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(REPORT_DIR, f'quality_report_{timestamp}.csv')
    
    # Write CSV report
    with open(report_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['check_name', 'failed_records', 'status', 'check_time'])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    # Write latest report
    latest_file = os.path.join(REPORT_DIR, 'quality_report_latest.csv')
    with open(latest_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['check_name', 'failed_records', 'status', 'check_time'])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    return report_file


def main():
    print("=" * 60)
    print("数据质量校验")
    print("=" * 60)
    
    # Connect to MySQL
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        database=MYSQL_DB,
        charset='utf8mb4'
    )
    
    # Run quality checks
    print("\n[1] 执行校验规则...")
    results = run_quality_checks(conn)
    
    # Generate report
    print("\n[2] 生成校验报告...")
    report_file = generate_report(results)
    print(f"  报告已保存: {report_file}")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    print("\n" + "=" * 60)
    print("校验汇总")
    print("=" * 60)
    print(f"  总计: {total} 项校验")
    print(f"  通过: {passed} 项")
    print(f"  失败: {failed} 项")
    print(f"  错误: {errors} 项")
    
    if failed > 0:
        print("\n  失败项详情:")
        for r in results:
            if r['status'] == 'FAIL':
                print(f"    ✗ {r['check_name']}: {r['failed_records']} 条异常")
    
    print("\n" + "=" * 60)
    if failed == 0 and errors == 0:
        print("  ✓ 数据质量校验全部通过!")
    else:
        print(f"  ✗ {failed} 项校验失败，请检查报告")
    print("=" * 60)
    
    conn.close()
    return failed == 0 and errors == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
