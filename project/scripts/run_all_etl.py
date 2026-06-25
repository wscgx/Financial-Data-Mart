import pymysql
import os
import sys
import time
import argparse
import io
from collections import defaultdict
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASS = '123456'
MYSQL_DB = 'financial_dw'

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
SQL_DIR = os.path.join(BASE_DIR, 'sql')
ETL_DIR = os.path.join(BASE_DIR, 'etl')

# ── ETL DAG 定义 ──────────────────────────────────────────────
# 格式: { etl_file: { "target": 表名, "deps": [依赖的ETL脚本], "sources": [读取的ODS表] }
ETL_DAG = {
    # ── Tier 1: DWD 层 (ODS → DWD) ──────────────────────────
    'etl_dwd_customer_asset_daily.sql': {
        'target': 'dwd_customer_asset_daily',
        'tier': 'dwd',
        'deps': [],
        'sources': ['ods_holding', 'ods_account', 'ods_customer', 'ods_transaction'],
    },
    'etl_dwd_customer_activity_daily.sql': {
        'target': 'dwd_customer_activity_daily',
        'tier': 'dwd',
        'deps': [],
        'sources': ['ods_transaction', 'ods_account', 'ods_customer', 'ods_product'],
    },
    'etl_dwd_customer_risk_match.sql': {
        'target': 'dwd_customer_risk_match',
        'tier': 'dwd',
        'deps': [],
        'sources': ['ods_holding', 'ods_account', 'ods_product', 'ods_risk_assessment'],
    },
    'etl_dwd_product_sales_daily.sql': {
        'target': 'dwd_product_sales_daily',
        'tier': 'dwd',
        'deps': [],
        'sources': ['ods_transaction', 'ods_product', 'ods_account'],
    },

    # ── Tier 2: DWS 层 (DWD/ODS → DWS) ──────────────────────
    'etl_dws_customer_value_profile.sql': {
        'target': 'dws_customer_value_profile',
        'tier': 'dws',
        'deps': ['etl_dwd_customer_asset_daily.sql'],
        'sources': ['dwd_customer_asset_daily', 'ods_customer'],
    },
    'etl_dws_customer_behavior_profile.sql': {
        'target': 'dws_customer_behavior_profile',
        'tier': 'dws',
        'deps': ['etl_dwd_customer_activity_daily.sql'],
        'sources': ['dwd_customer_activity_daily', 'ods_customer'],
    },
    'etl_dws_risk_compliance_summary.sql': {
        'target': 'dws_risk_compliance_summary',
        'tier': 'dws',
        'deps': ['etl_dwd_customer_risk_match.sql'],
        'sources': ['dwd_customer_risk_match', 'ods_customer'],
    },
    'etl_dws_product_performance.sql': {
        'target': 'dws_product_performance',
        'tier': 'dws',
        'deps': ['etl_dwd_product_sales_daily.sql'],
        'sources': ['dwd_product_sales_daily', 'ods_product'],
    },
    'etl_dws_platform_daily_summary.sql': {
        'target': 'dws_platform_daily_summary',
        'tier': 'dws',
        'deps': ['etl_dwd_customer_asset_daily.sql', 'etl_dwd_customer_activity_daily.sql'],
        'sources': ['dwd_customer_asset_daily', 'dwd_customer_activity_daily', 'ods_product'],
    },

    # ── Tier 3: ADS 层 (DWD/DWS/ODS → ADS) ──────────────────
    'etl_ads_executive_dashboard.sql': {
        'target': 'ads_executive_dashboard',
        'tier': 'ads',
        'deps': ['etl_dws_platform_daily_summary.sql'],
        'sources': ['dws_platform_daily_summary', 'ods_transaction', 'ods_account'],
    },
    'etl_ads_customer_churn_warning.sql': {
        'target': 'ads_customer_churn_warning',
        'tier': 'ads',
        'deps': ['etl_dws_customer_behavior_profile.sql'],
        'sources': ['dws_customer_behavior_profile'],
    },
    'etl_ads_customer_value_level_dist.sql': {
        'target': 'ads_customer_value_level_dist',
        'tier': 'ads',
        'deps': ['etl_dws_customer_value_profile.sql'],
        'sources': ['dws_customer_value_profile'],
    },
    'etl_ads_customer_aum_ranking.sql': {
        'target': 'ads_customer_aum_ranking',
        'tier': 'ads',
        'deps': ['etl_dws_customer_value_profile.sql'],
        'sources': ['dws_customer_value_profile'],
    },
    'etl_ads_risk_mismatch_alert.sql': {
        'target': 'ads_risk_mismatch_alert',
        'tier': 'ads',
        'deps': ['etl_dwd_customer_risk_match.sql'],
        'sources': ['dwd_customer_risk_match', 'ods_customer'],
    },
    'etl_ads_anomaly_detection.sql': {
        'target': 'ads_anomaly_detection',
        'tier': 'ads',
        'deps': ['etl_dws_platform_daily_summary.sql', 'etl_dwd_customer_asset_daily.sql'],
        'sources': ['dws_platform_daily_summary', 'ods_transaction', 'dwd_customer_asset_daily'],
    },
    'etl_ads_customer_net_asset_change.sql': {
        'target': 'ads_customer_net_asset_change',
        'tier': 'ads',
        'deps': ['etl_dwd_customer_asset_daily.sql'],
        'sources': ['dwd_customer_asset_daily', 'ods_customer'],
    },
    'etl_ads_customer_aum_daily.sql': {
        'target': 'ads_customer_aum_daily',
        'tier': 'ads',
        'deps': ['etl_dwd_customer_asset_daily.sql'],
        'sources': ['dwd_customer_asset_daily', 'ods_customer'],
    },
    'etl_ads_multi_dimension_analysis.sql': {
        'target': 'ads_multi_dimension_analysis',
        'tier': 'ads',
        'deps': ['etl_dwd_customer_asset_daily.sql'],
        'sources': ['dwd_customer_asset_daily', 'ods_customer', 'ods_transaction',
                     'ods_account', 'ods_product', 'ods_holding', 'ods_risk_assessment'],
    },
    'etl_ads_branch_sales_ranking.sql': {
        'target': 'ads_branch_sales_ranking',
        'tier': 'ads',
        'deps': [],
        'sources': ['ods_transaction', 'ods_account'],
    },
    'etl_ads_avg_daily_aum_monthly.sql': {
        'target': 'ads_avg_daily_aum_monthly',
        'tier': 'ads',
        'deps': ['etl_dwd_customer_asset_daily.sql'],
        'sources': ['dwd_customer_asset_daily', 'ods_customer'],
    },
    'etl_ads_risk_metrics_daily.sql': {
        'target': 'ads_risk_metrics_daily',
        'tier': 'ads',
        'deps': ['etl_dwd_customer_risk_match.sql', 'etl_dws_risk_compliance_summary.sql',
                 'etl_ads_risk_mismatch_alert.sql'],
        'sources': ['dwd_customer_risk_match', 'dws_risk_compliance_summary', 'ads_risk_mismatch_alert'],
    },

    # ── 指标定义表 (静态数据) ─────────────────────────────────
}


def read_sql_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def execute_sql(cursor, sql_text):
    lines = [line for line in sql_text.split('\n') if not line.strip().startswith('--')]
    clean_sql = '\n'.join(lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    total_rows = 0
    for stmt in statements:
        cursor.execute(stmt)
        total_rows += cursor.rowcount
    return total_rows


def topological_sort(dag):
    visited = set()
    order = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for dep in dag[node]['deps']:
            if dep in dag:
                dfs(dep)
        order.append(node)

    for node in dag:
        dfs(node)
    return order


def run_etl_pipeline(tiers=None, options=None, skip_ddl=False, dry_run=False):
    start_time = time.time()
    print("=" * 70)
    print(f"  全量 ETL 执行  -  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 按 tier 过滤
    if tiers:
        tiers = [t.lower() for t in tiers]
        target_etls = {k: v for k, v in ETL_DAG.items() if v['tier'] in tiers}
    else:
        target_etls = dict(ETL_DAG)

    # 按 option 过滤 (映射关系)
    if options:
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
            opt = opt.lower()
            if opt in option_map:
                selected.update(option_map[opt])
        # 包含被依赖的脚本
        changed = True
        while changed:
            changed = False
            for etl_file in list(selected):
                for dep in ETL_DAG[etl_file]['deps']:
                    if dep not in selected and dep in ETL_DAG:
                        selected.add(dep)
                        changed = True
        target_etls = {k: v for k, v in ETL_DAG.items() if k in selected}

    # 拓扑排序
    exec_order = [e for e in topological_sort(target_etls) if e in target_etls]
    print(f"\n执行计划: {len(exec_order)} 个 ETL 任务")
    print("-" * 70)
    for i, etl in enumerate(exec_order, 1):
        info = target_etls[etl]
        deps_str = ', '.join(info['deps']) if info['deps'] else '(无)'
        print(f"  {i:2d}. [{info['tier'].upper():3s}] {etl}")
        print(f"      目标: {info['target']}  |  依赖: {deps_str}")
    print("-" * 70)

    if dry_run:
        print("\n[Dry Run] 仅展示执行计划，不实际执行")
        return

    # 连接数据库
    conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                           password=MYSQL_PASS, database=MYSQL_DB, charset='utf8mb4')
    cursor = conn.cursor()

    # 可选: 创建 DDL
    if not skip_ddl:
        print("\n[DDL] 创建表结构...")
        ddl_created = 0
        for etl_file in exec_order:
            target = target_etls[etl_file]['target']
            tier = target_etls[etl_file]['tier']
            ddl_path = os.path.join(SQL_DIR, tier, f'{target}.sql')
            if os.path.exists(ddl_path):
                try:
                    sql_text = read_sql_file(ddl_path)
                    execute_sql(cursor, sql_text)
                    conn.commit()
                    ddl_created += 1
                except Exception as e:
                    if 'Duplicate key' not in str(e) and '1061' not in str(e):
                        print(f"  ⚠ DDL 警告 {target}: {e}")
        print(f"  ✓ DDL 完成 ({ddl_created} 张表)")

    # 执行 ETL
    print("\n[ETL] 开始执行数据加工...")
    results = []
    success_count = 0
    fail_count = 0

    for i, etl_file in enumerate(exec_order, 1):
        info = target_etls[etl_file]
        etl_path = os.path.join(ETL_DIR, etl_file)
        target = info['target']
        tier = info['tier'].upper()

        print(f"\n  [{i:2d}/{len(exec_order)}] {tier} → {target}")
        print(f"       脚本: {etl_file}")

        t0 = time.time()
        try:
            sql_text = read_sql_file(etl_path)
            rows = execute_sql(cursor, sql_text)
            conn.commit()
            elapsed = time.time() - t0

            # 验证行数
            cursor.execute(f"SELECT COUNT(*) FROM {target}")
            total = cursor.fetchone()[0]

            print(f"       ✓ 影响 {rows:,} 行, 总计 {total:,} 行  ({elapsed:.1f}s)")
            results.append({'etl': etl_file, 'target': target, 'status': 'OK',
                            'rows': rows, 'total': total, 'time': elapsed})
            success_count += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"       ✗ 失败: {e}")
            results.append({'etl': etl_file, 'target': target, 'status': 'FAIL',
                            'error': str(e), 'time': elapsed})
            fail_count += 1
            conn.rollback()

    conn.close()

    # 汇总
    elapsed_total = time.time() - start_time
    print("\n" + "=" * 70)
    print("  ETL 执行汇总")
    print("=" * 70)
    print(f"  成功: {success_count}  |  失败: {fail_count}  |  总耗时: {elapsed_total:.1f}s")
    print()

    if fail_count > 0:
        print("  失败任务:")
        for r in results:
            if r['status'] == 'FAIL':
                print(f"    ✗ {r['target']}: {r.get('error', 'unknown')}")
        print()

    print("  各层数据量:")
    for r in results:
        if r['status'] == 'OK':
            print(f"    {r['target']:<40s} {r['total']:>10,} 行")

    print("\n" + "=" * 70)
    if fail_count == 0:
        print("  ✓ 全部 ETL 执行成功!")
    else:
        print(f"  ✗ {fail_count} 个任务失败，请检查日志")
    print("=" * 70)

    return fail_count == 0


def main():
    parser = argparse.ArgumentParser(description='全量 ETL 执行器 - 按 DAG 依赖顺序')
    parser.add_argument('--tier', nargs='+', choices=['dwd', 'dws', 'ads'],
                        help='仅执行指定层级 (可多选, 如 --tier dwd dws)')
    parser.add_argument('--option', nargs='+', choices=['a', 'b', 'c', 'd', 'e'],
                        help='仅执行指定业务选项 (自动包含依赖, 如 --option a b)')
    parser.add_argument('--skip-ddl', action='store_true',
                        help='跳过 DDL 建表 (表已存在时)')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅展示执行计划，不实际执行')
    parser.add_argument('--show-dag', action='store_true',
                        help='展示完整 DAG 依赖关系图')
    args = parser.parse_args()

    if args.show_dag:
        print("ETL DAG 依赖关系图:")
        print("=" * 70)
        for tier_name in ['dwd', 'dws', 'ads']:
            tier_etls = {k: v for k, v in ETL_DAG.items() if v['tier'] == tier_name}
            if tier_etls:
                print(f"\n[{tier_name.upper()} 层]")
                for etl, info in tier_etls.items():
                    deps = ', '.join(info['deps']) if info['deps'] else '(无)'
                    print(f"  {etl}")
                    print(f"    → {info['target']}  deps: {deps}")
        return

    success = run_etl_pipeline(
        tiers=args.tier,
        options=args.option,
        skip_ddl=args.skip_ddl,
        dry_run=args.dry_run,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
