"""
Spark / MinIO / Delta Lake 连接配置
"""
import os

# ── MinIO (S3) 配置 ─────────────────────────────────────────
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# 数据湖 Bucket
DATA_LAKE_BUCKET = "financial-data-lake"
ODS_PATH = f"s3a://{DATA_LAKE_BUCKET}/ods"
DWD_PATH = f"s3a://{DATA_LAKE_BUCKET}/dwd"
DWS_PATH = f"s3a://{DATA_LAKE_BUCKET}/dws"
ADS_PATH = f"s3a://{DATA_LAKE_BUCKET}/ads"
WAREHOUSE_PATH = f"s3a://{DATA_LAKE_BUCKET}/warehouse"
CHECKPOINTS_PATH = f"s3a://{DATA_LAKE_BUCKET}/checkpoints"

# ── MySQL 配置 ──────────────────────────────────────────────
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "financial_dw")
MYSQL_URL = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?useUnicode=true&characterEncoding=utf8mb4"
MYSQL_PROPERTIES = {
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "driver": "com.mysql.cj.jdbc.Driver",
}

# ── Kafka 配置 ──────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "financial_transactions")

# ── Spark Master 配置 ──────────────────────────────────────
SPARK_MASTER = os.getenv("SPARK_MASTER", "spark://spark-master:7077")


def get_spark_session(app_name="FinancialDW", master=None):
    """创建 SparkSession，集成 Delta Lake 和 MinIO"""
    from pyspark.sql import SparkSession

    if master is None:
        master = SPARK_MASTER

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.jars.packages",
                "io.delta:delta-spark_2.12:3.0.0,"
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.mysql:mysql-connector-j:8.0.33")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.sql.warehouse.dir", WAREHOUSE_PATH)
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark


def read_mysql_table(spark, table_name):
    """从 MySQL 读取表到 Spark DataFrame"""
    return (
        spark.read
        .format("jdbc")
        .option("url", MYSQL_URL)
        .option("dbtable", table_name)
        .options(**MYSQL_PROPERTIES)
        .load()
    )


def write_delta_table(df, path, mode="overwrite", partition_by=None):
    """将 DataFrame 写入 Delta Lake"""
    writer = df.write.format("delta").mode(mode)
    if partition_by:
        writer = writer.partitionBy(partition_by)
    writer.save(path)


def merge_delta_table(spark, source_df, target_path, merge_condition):
    """Delta Lake MERGE (增量更新)"""
    from delta.tables import DeltaTable

    delta_table = DeltaTable.forPath(spark, target_path)

    (
        delta_table.alias("target")
        .merge(source_df.alias("source"), merge_condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def read_delta_table(spark, path):
    """从 Delta Lake 读取表"""
    return spark.read.format("delta").load(path)


def write_to_mysql(df, table_name, mode="overwrite"):
    """将 DataFrame 写入 MySQL"""
    (
        df.write
        .format("jdbc")
        .option("url", MYSQL_URL)
        .option("dbtable", table_name)
        .options(**MYSQL_PROPERTIES)
        .mode(mode)
        .save()
    )


def get_kafka_producer_config():
    """获取 Kafka 生产者配置"""
    return {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "financial_producer",
    }


def get_kafka_consumer_config(group_id="financial_consumer"):
    """获取 Kafka 消费者配置"""
    return {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": group_id,
        "auto.offset.reset": "latest",
    }
