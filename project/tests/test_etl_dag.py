import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from run_all_etl import ETL_DAG, topological_sort, read_sql_file, execute_sql, ETL_DIR, SQL_DIR


class TestDAGIntegrity(unittest.TestCase):
    """验证 ETL DAG 定义的完整性和正确性"""

    def test_all_etl_files_exist(self):
        """所有 DAG 中声明的 ETL 脚本文件必须存在"""
        missing = []
        for etl_file in ETL_DAG:
            path = os.path.join(ETL_DIR, etl_file)
            if not os.path.exists(path):
                missing.append(etl_file)
        self.assertEqual(missing, [], f"Missing ETL files: {missing}")

    def test_no_self_dependency(self):
        """没有脚本依赖自身"""
        for etl_file, info in ETL_DAG.items():
            self.assertNotIn(etl_file, info['deps'],
                             f"{etl_file} depends on itself")

    def test_all_deps_exist_in_dag(self):
        """所有依赖项必须在 DAG 中定义"""
        for etl_file, info in ETL_DAG.items():
            for dep in info['deps']:
                self.assertIn(dep, ETL_DAG,
                              f"{etl_file} depends on {dep}, which is not in DAG")

    def test_target_tables_are_unique(self):
        """每个 ETL 脚本的目标表必须唯一"""
        targets = [info['target'] for info in ETL_DAG.values()]
        duplicates = [t for t in targets if targets.count(t) > 1]
        self.assertEqual(duplicates, [], f"Duplicate target tables: {set(duplicates)}")

    def test_tier_values_valid(self):
        """所有 tier 值必须是 dwd/dws/ads 之一"""
        valid_tiers = {'dwd', 'dws', 'ads'}
        for etl_file, info in ETL_DAG.items():
            self.assertIn(info['tier'], valid_tiers,
                          f"{etl_file} has invalid tier: {info['tier']}")

    def test_all_ddl_files_exist(self):
        """每个目标表对应的 DDL 文件必须存在"""
        missing = []
        for etl_file, info in ETL_DAG.items():
            tier = info['tier']
            target = info['target']
            ddl_path = os.path.join(SQL_DIR, tier, f'{target}.sql')
            if not os.path.exists(ddl_path):
                missing.append(f"{tier}/{target}.sql")
        self.assertEqual(missing, [], f"Missing DDL files: {missing}")


class TestTopologicalSort(unittest.TestCase):
    """验证拓扑排序的正确性"""

    def test_dwd_before_dws(self):
        """DWD 层必须排在 DWS 层之前"""
        order = topological_sort(ETL_DAG)
        dwd_end = max(i for i, e in enumerate(order) if ETL_DAG[e]['tier'] == 'dwd')
        dws_start = min(i for i, e in enumerate(order) if ETL_DAG[e]['tier'] == 'dws')
        self.assertLess(dwd_end, dws_start,
                        "DWD layer should execute before DWS layer")

    def test_dws_before_ads(self):
        """DWS 层必须排在 ADS 层之前"""
        order = topological_sort(ETL_DAG)
        dws_end = max(i for i, e in enumerate(order) if ETL_DAG[e]['tier'] == 'dws')
        ads_start = min(i for i, e in enumerate(order) if ETL_DAG[e]['tier'] == 'ads')
        self.assertLess(dws_end, ads_start,
                        "DWS layer should execute before ADS layer")

    def test_deps_come_before_dependents(self):
        """每个脚本的所有依赖必须排在它之前"""
        order = topological_sort(ETL_DAG)
        for i, etl in enumerate(order):
            for dep in ETL_DAG[etl]['deps']:
                if dep in ETL_DAG:
                    dep_idx = order.index(dep)
                    self.assertLess(dep_idx, i,
                                    f"{dep} should come before {etl}")

    def test_all_tasks_included(self):
        """排序结果必须包含所有 DAG 中的任务"""
        order = topological_sort(ETL_DAG)
        self.assertEqual(set(order), set(ETL_DAG.keys()))

    def test_no_duplicates(self):
        """排序结果不能有重复"""
        order = topological_sort(ETL_DAG)
        self.assertEqual(len(order), len(set(order)))

    def test_dwd_no_deps(self):
        """DWD 层脚本不应有 DAG 内依赖"""
        for etl_file, info in ETL_DAG.items():
            if info['tier'] == 'dwd':
                dag_deps = [d for d in info['deps'] if d in ETL_DAG]
                self.assertEqual(dag_deps, [],
                                 f"DWD script {etl_file} has unexpected DAG deps: {dag_deps}")

    def test_risk_metrics_is_last(self):
        """ads_risk_metrics_daily 应该排在所有 risk 相关脚本之后"""
        order = topological_sort(ETL_DAG)
        risk_etls = [e for e in order if 'risk' in e]
        self.assertGreater(len(risk_etls), 0)
        self.assertEqual(risk_etls[-1], 'etl_ads_risk_metrics_daily.sql')


class TestOptionFilter(unittest.TestCase):
    """验证按 option 过滤时依赖自动拉取"""

    def _resolve_option(self, options):
        option_map = {
            'a': ['etl_dwd_customer_asset_daily.sql', 'etl_dws_customer_value_profile.sql',
                  'etl_ads_customer_aum_daily.sql', 'etl_ads_customer_aum_ranking.sql',
                  'etl_ads_customer_value_level_dist.sql', 'etl_ads_customer_net_asset_change.sql',
                  'etl_ads_avg_daily_aum_monthly.sql'],
            'b': ['etl_dwd_product_sales_daily.sql', 'etl_dws_product_performance.sql',
                  'etl_ads_branch_sales_ranking.sql'],
            'c': ['etl_dwd_customer_risk_match.sql', 'etl_dws_risk_compliance_summary.sql',
                  'etl_ads_risk_mismatch_alert.sql', 'etl_ads_risk_metrics_daily.sql'],
            'd': ['etl_dwd_customer_activity_daily.sql', 'etl_dws_customer_behavior_profile.sql',
                  'etl_ads_customer_churn_warning.sql'],
            'e': ['etl_dws_platform_daily_summary.sql', 'etl_ads_executive_dashboard.sql',
                  'etl_ads_multi_dimension_analysis.sql', 'etl_ads_anomaly_detection.sql'],
        }
        selected = set()
        for opt in options:
            if opt in option_map:
                selected.update(option_map[opt])
        changed = True
        while changed:
            changed = False
            for etl_file in list(selected):
                for dep in ETL_DAG[etl_file]['deps']:
                    if dep not in selected and dep in ETL_DAG:
                        selected.add(dep)
                        changed = True
        return selected

    def test_option_a_includes_asset_dwd(self):
        """选项A应自动包含其DWD依赖"""
        selected = self._resolve_option(['a'])
        self.assertIn('etl_dwd_customer_asset_daily.sql', selected)

    def test_option_c_includes_all_risk_chain(self):
        """选项C应包含完整风险链 (DWD→DWS→ADS)"""
        selected = self._resolve_option(['c'])
        self.assertIn('etl_dwd_customer_risk_match.sql', selected)
        self.assertIn('etl_dws_risk_compliance_summary.sql', selected)
        self.assertIn('etl_ads_risk_mismatch_alert.sql', selected)
        self.assertIn('etl_ads_risk_metrics_daily.sql', selected)

    def test_option_e_includes_platform_dws_deps(self):
        """选项E的platform_summary依赖两个DWD"""
        selected = self._resolve_option(['e'])
        self.assertIn('etl_dwd_customer_asset_daily.sql', selected)
        self.assertIn('etl_dwd_customer_activity_daily.sql', selected)

    def test_option_d_all_deps_satisfied(self):
        """选项D选出的脚本，其所有依赖都在集合内"""
        selected = self._resolve_option(['d'])
        for etl in selected:
            for dep in ETL_DAG[etl]['deps']:
                if dep in ETL_DAG:
                    self.assertIn(dep, selected,
                                  f"{etl} depends on {dep} but it's not included")


class TestReadSqlFile(unittest.TestCase):
    """验证 SQL 文件读取"""

    def test_read_etl_file(self):
        """能正确读取 ETL SQL 文件"""
        content = read_sql_file(os.path.join(ETL_DIR, 'etl_dwd_customer_asset_daily.sql'))
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)

    def test_read_ddl_file(self):
        """能正确读取 DDL 文件"""
        content = read_sql_file(os.path.join(SQL_DIR, 'dwd', 'dwd_customer_asset_daily.sql'))
        self.assertIsInstance(content, str)
        self.assertIn('CREATE TABLE', content.upper())


if __name__ == '__main__':
    unittest.main()
