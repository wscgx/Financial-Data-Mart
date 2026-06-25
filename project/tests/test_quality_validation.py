import unittest
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from run_quality_validation import VALIDATION_QUERIES


class TestValidationRulesStructure(unittest.TestCase):
    """验证数据质量校验规则的结构完整性"""

    def test_all_rules_have_required_fields(self):
        for rule in VALIDATION_QUERIES:
            self.assertIn('name', rule)
            self.assertIn('desc', rule)
            self.assertIn('sql', rule)

    def test_rule_names_are_unique(self):
        from collections import Counter
        names = [r['name'] for r in VALIDATION_QUERIES]
        counts = Counter(names)
        duplicates = {n: c for n, c in counts.items() if c > 2}
        self.assertEqual(duplicates, {}, f"Rule names duplicated >2 times: {duplicates}")

    def test_rule_names_not_empty(self):
        for rule in VALIDATION_QUERIES:
            self.assertGreater(len(rule['name']), 0)

    def test_rule_desc_not_empty(self):
        for rule in VALIDATION_QUERIES:
            self.assertGreater(len(rule['desc']), 0)

    def test_rule_sql_not_empty(self):
        for rule in VALIDATION_QUERIES:
            self.assertGreater(len(rule['sql'].strip()), 0)

    def test_rule_names_follow_convention(self):
        valid_prefixes = ('dwd_', 'dws_', 'ads_', 'dwd_dws_', 'missing_')
        for rule in VALIDATION_QUERIES:
            name = rule['name']
            has_valid_prefix = any(name.startswith(p) for p in valid_prefixes)
            self.assertTrue(has_valid_prefix, f"Rule name '{name}' doesn't follow naming convention")


class TestValidationSQLSyntax(unittest.TestCase):
    """验证校验 SQL 的基本语法正确性"""

    def test_sql_contains_select(self):
        for rule in VALIDATION_QUERIES:
            sql = rule['sql'].strip().upper()
            self.assertTrue(sql.startswith('SELECT'),
                            f"Rule '{rule['name']}' SQL doesn't start with SELECT")

    def test_sql_selects_failed_records(self):
        for rule in VALIDATION_QUERIES:
            sql_upper = rule['sql'].upper()
            has_count = 'COUNT(*)' in sql_upper or 'FAILED_RECORDS' in sql_upper
            self.assertTrue(has_count,
                            f"Rule '{rule['name']}' should SELECT COUNT(*) or failed_records")

    def test_sql_references_known_tables(self):
        known_tables = {
            'ods_customer', 'ods_account', 'ods_product', 'ods_transaction',
            'ods_holding', 'ods_risk_assessment',
            'dwd_customer_asset_daily', 'dwd_customer_activity_daily',
            'dwd_customer_risk_match', 'dwd_product_sales_daily',
            'dws_customer_value_profile', 'dws_customer_behavior_profile',
            'dws_risk_compliance_summary', 'dws_product_performance',
            'dws_platform_daily_summary',
            'ads_customer_aum_ranking', 'ads_customer_aum_daily',
            'ads_customer_value_level_dist', 'ads_customer_net_asset_change',
            'ads_avg_daily_aum_monthly', 'ads_branch_sales_ranking',
            'ads_customer_churn_warning', 'ads_risk_mismatch_alert',
            'ads_risk_metrics_daily', 'ads_executive_dashboard',
            'ads_multi_dimension_analysis', 'ads_anomaly_detection',
        }
        for rule in VALIDATION_QUERIES:
            sql_upper = rule['sql'].upper()
            for table in re.findall(r'FROM\s+(\w+)', sql_upper):
                if table.lower() not in known_tables and not table.startswith('('):
                    self.fail(f"Rule '{rule['name']}' references unknown table: {table}")


class TestValidationCoverage(unittest.TestCase):
    """验证校验规则覆盖所有层级"""

    def test_has_dwd_rules(self):
        dwd_rules = [r for r in VALIDATION_QUERIES if r['name'].startswith('dwd_')]
        self.assertGreater(len(dwd_rules), 0)

    def test_has_dws_rules(self):
        dws_rules = [r for r in VALIDATION_QUERIES if r['name'].startswith('dws_')]
        self.assertGreater(len(dws_rules), 0)

    def test_has_ads_rules(self):
        ads_rules = [r for r in VALIDATION_QUERIES if r['name'].startswith('ads_')]
        self.assertGreater(len(ads_rules), 0)

    def test_has_cross_layer_rules(self):
        cross_rules = [r for r in VALIDATION_QUERIES if 'dwd_dws' in r['name']]
        self.assertGreater(len(cross_rules), 0)

    def test_has_completeness_rules(self):
        completeness_rules = [r for r in VALIDATION_QUERIES if 'missing' in r['name']]
        self.assertGreater(len(completeness_rules), 0)


if __name__ == '__main__':
    unittest.main()
