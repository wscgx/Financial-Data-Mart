"""
Airflow DAG: 金融数据仓库 ETL 调度

替代现有 run_all_etl.py 的手动调度方式
支持按层级、按业务选项过滤执行
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# ── 默认参数 ────────────────────────────────────────────────
default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# ── DAG 定义 ────────────────────────────────────────────────
with DAG(
    dag_id="financial_etl_pipeline",
    default_args=default_args,
    description="金融数据仓库全量 ETL 调度 (ODS → DWD → DWS → ADS)",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["financial", "etl"],
) as dag:

    start = EmptyOperator(task_id="start")

    # ── Tier 1: DWD 层 ──────────────────────────────────────
    dwd_customer_asset = EmptyOperator(task_id="dwd_customer_asset_daily")
    dwd_customer_activity = EmptyOperator(task_id="dwd_customer_activity_daily")
    dwd_customer_risk = EmptyOperator(task_id="dwd_customer_risk_match")
    dwd_product_sales = EmptyOperator(task_id="dwd_product_sales_daily")

    # ── Tier 2: DWS 层 ──────────────────────────────────────
    dws_customer_value = EmptyOperator(task_id="dws_customer_value_profile")
    dws_customer_behavior = EmptyOperator(task_id="dws_customer_behavior_profile")
    dws_risk_compliance = EmptyOperator(task_id="dws_risk_compliance_summary")
    dws_product_performance = EmptyOperator(task_id="dws_product_performance")
    dws_platform_summary = EmptyOperator(task_id="dws_platform_daily_summary")

    # ── Tier 3: ADS 层 ──────────────────────────────────────
    ads_executive = EmptyOperator(task_id="ads_executive_dashboard")
    ads_churn = EmptyOperator(task_id="ads_customer_churn_warning")
    ads_value_dist = EmptyOperator(task_id="ads_customer_value_level_dist")
    ads_aum_ranking = EmptyOperator(task_id="ads_customer_aum_ranking")
    ads_risk_alert = EmptyOperator(task_id="ads_risk_mismatch_alert")
    ads_anomaly = EmptyOperator(task_id="ads_anomaly_detection")
    ads_net_change = EmptyOperator(task_id="ads_customer_net_asset_change")
    ads_aum_daily = EmptyOperator(task_id="ads_customer_aum_daily")
    ads_multi_dim = EmptyOperator(task_id="ads_multi_dimension_analysis")
    ads_branch_rank = EmptyOperator(task_id="ads_branch_sales_ranking")
    ads_avg_daily = EmptyOperator(task_id="ads_avg_daily_aum_monthly")
    ads_risk_metrics = EmptyOperator(task_id="ads_risk_metrics_daily")

    end = EmptyOperator(task_id="end", trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

    # ── DAG 依赖关系 ─────────────────────────────────────────

    # DWD 层: ODS → DWD (无内部依赖，可并行)
    start >> [dwd_customer_asset, dwd_customer_activity, dwd_customer_risk, dwd_product_sales]

    # DWS 层: DWD → DWS
    dwd_customer_asset >> dws_customer_value
    dwd_customer_activity >> dws_customer_behavior
    dwd_customer_risk >> dws_risk_compliance
    dwd_product_sales >> dws_product_performance
    [dwd_customer_asset, dwd_customer_activity] >> dws_platform_summary

    # ADS 层: DWS/DWD → ADS
    dws_platform_summary >> ads_executive
    dws_customer_behavior >> ads_churn
    dws_customer_value >> ads_value_dist
    dws_customer_value >> ads_aum_ranking
    dwd_customer_risk >> ads_risk_alert
    [dws_platform_summary, dwd_customer_asset] >> ads_anomaly
    dwd_customer_asset >> ads_net_change
    dwd_customer_asset >> ads_aum_daily
    dwd_customer_asset >> ads_multi_dim
    [dwd_customer_asset, dws_customer_value] >> ads_avg_daily
    [dws_risk_compliance, ads_risk_alert] >> ads_risk_metrics

    # 汇总
    [ads_executive, ads_churn, ads_value_dist, ads_aum_ranking,
     ads_risk_alert, ads_anomaly, ads_net_change, ads_aum_daily,
     ads_multi_dim, ads_branch_rank, ads_avg_daily, ads_risk_metrics] >> end
