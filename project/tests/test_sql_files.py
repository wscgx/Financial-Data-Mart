import unittest
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
SQL_DIR = os.path.join(BASE_DIR, 'sql')
ETL_DIR = os.path.join(BASE_DIR, 'etl')


class TestDDLFiles(unittest.TestCase):
    """验证 DDL 文件的 MySQL 语法"""

    def _find_ddl_files(self):
        files = []
        for tier in ['ods', 'dwd', 'dws', 'ads']:
            tier_dir = os.path.join(SQL_DIR, tier)
            if os.path.exists(tier_dir):
                for f in os.listdir(tier_dir):
                    if f.endswith('.sql'):
                        files.append(os.path.join(tier_dir, f))
        return files

    def test_ddl_files_exist(self):
        files = self._find_ddl_files()
        self.assertGreater(len(files), 0, "No DDL files found")

    def test_ddl_contains_create_table(self):
        for filepath in self._find_ddl_files():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().upper()
            self.assertIn('CREATE TABLE', content,
                          f"DDL file missing CREATE TABLE: {os.path.basename(filepath)}")

    def test_ddl_has_engine_innodb(self):
        for filepath in self._find_ddl_files():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().upper()
            self.assertIn('ENGINE=INNODB', content,
                          f"DDL file missing ENGINE=InnoDB: {os.path.basename(filepath)}")

    def test_ddl_has_charset_utf8mb4(self):
        for filepath in self._find_ddl_files():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().upper()
            self.assertIn('UTF8MB4', content,
                          f"DDL file missing utf8mb4: {os.path.basename(filepath)}")

    def test_ddl_has_comment(self):
        for filepath in self._find_ddl_files():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().upper()
            self.assertTrue('COMMENT' in content,
                            f"DDL file missing COMMENT: {os.path.basename(filepath)}")


class TestETLFiles(unittest.TestCase):
    """验证 ETL 文件存在且可读"""

    def test_etl_files_exist(self):
        etl_files = [f for f in os.listdir(ETL_DIR) if f.endswith('.sql')]
        self.assertGreater(len(etl_files), 0, "No ETL files found")

    def test_etl_files_are_readable(self):
        for f in os.listdir(ETL_DIR):
            if f.endswith('.sql'):
                filepath = os.path.join(ETL_DIR, f)
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                self.assertGreater(len(content), 0, f"ETL file is empty: {f}")

    def test_etl_files_have_insert(self):
        for f in os.listdir(ETL_DIR):
            if f.endswith('.sql'):
                filepath = os.path.join(ETL_DIR, f)
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read().upper()
                self.assertTrue('INSERT' in content,
                                f"ETL file missing INSERT: {f}")


class TestETLDAGConsistency(unittest.TestCase):
    """验证 ETL DAG 与实际文件的一致性"""

    def test_all_etl_files_have_ddl(self):
        from run_all_etl import ETL_DAG
        missing = []
        for etl_file, info in ETL_DAG.items():
            ddl_path = os.path.join(SQL_DIR, info['tier'], f"{info['target']}.sql")
            if not os.path.exists(ddl_path):
                missing.append(f"{info['tier']}/{info['target']}.sql")
        self.assertEqual(missing, [], f"Missing DDL files: {missing}")

    def test_no_cycles_in_dag(self):
        from run_all_etl import ETL_DAG
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for dep in ETL_DAG[node]['deps']:
                if dep in ETL_DAG:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            rec_stack.discard(node)
            return False

        for node in ETL_DAG:
            if node not in visited:
                self.assertFalse(has_cycle(node), f"Cycle detected involving {node}")


if __name__ == '__main__':
    unittest.main()
