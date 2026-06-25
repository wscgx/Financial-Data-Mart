"""
Airflow DAG: 金融数据仓库 ETL 调度 (Delta Lake 版本)

支持 PySpark 脚本执行，通过 SparkSubmitOperator 提交到 Spark 集群
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
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

# ── Spark 配置 ──────────────────────────────────────────────
SPARK_CONN_ID = "spark_default"
SPARK_HOME = "/opt/bitnami/spark"
PYTHON_PATH = "/opt/airflow/dags/scripts"

# ── DAG 定义 ────────────────────────────────────────────────
with DAG(
    dag_id="financial_etl_pipeline_delta",
    default_args=default_args,
    description="金融数据仓库 ETL 调度 (MySQL → Delta Lake → MySQL)",
    schedule_interval="0 2 * * *",  # 每日凌晨2点
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["financial", "etl", "delta"],
) as dag:

    start = EmptyOperator(task_id="start")

    # ── Phase 1: ODS 层 (MySQL → Delta Lake) ────────────────
    ods_sync = SparkSubmitOperator(
        task_id="ods_mysql_to_delta",
        application=f"{PYTHON_PATH}/etl_ods_to_delta.py",
        conn_id=SPARK_CONN_ID,
        application_args=["--date", "{{ ds }}"],
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        },
    )

    # ── Phase 2: DWD 层 (Delta ODS → Delta DWD) ────────────
    dwd_build = SparkSubmitOperator(
        task_id="dwd_delta_to_delta",
        application=f"{PYTHON_PATH}/etl_dwd_to_delta.py",
        conn_id=SPARK_CONN_ID,
        application_args=["--date", "{{ ds }}"],
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        },
    )

    # ── Phase 3: DWS 层 (Delta DWD → Delta DWS) ────────────
    dws_build = SparkSubmitOperator(
        task_id="dws_delta_to_delta",
        application=f"{PYTHON_PATH}/etl_dws_to_delta.py",
        conn_id=SPARK_CONN_ID,
        application_args=["--date", "{{ ds }}"],
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        },
    )

    # ── Phase 4: ADS 层 (Delta DWS/DWD → Delta ADS) ────────
    ads_build = SparkSubmitOperator(
        task_id="ads_delta_to_delta",
        application=f"{PYTHON_PATH}/etl_ads_to_delta.py",
        conn_id=SPARK_CONN_ID,
        application_args=["--date", "{{ ds }}"],
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        },
    )

    # ── Phase 5: ADS → MySQL 回写 ──────────────────────────
    ads_sync = SparkSubmitOperator(
        task_id="ads_sync_to_mysql",
        application=f"{PYTHON_PATH}/etl_ads_sync_mysql.py",
        conn_id=SPARK_CONN_ID,
        application_args=["--date", "{{ ds }}"],
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        },
    )

    # ── Phase 6: 数据质量校验 ──────────────────────────────
    quality_check = EmptyOperator(task_id="data_quality_check")

    end = EmptyOperator(task_id="end", trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

    # ── DAG 依赖关系 ─────────────────────────────────────────
    start >> ods_sync >> dwd_build >> dws_build >> ads_build >> ads_sync >> quality_check >> end
