"""
ETL 指标导出器 - 将 ETL 执行指标暴露给 Prometheus

用法:
    python etl_metrics_exporter.py

功能:
    启动一个 HTTP 服务，暴露 ETL 任务执行指标
    Prometheus 定期抓取这些指标
"""
import time
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pymysql

METRICS_PORT = 9100

# ── MySQL 配置 ──────────────────────────────────────────────
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "financial_dw")


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics = {
            "etl_task_total": 0,
            "etl_task_success": 0,
            "etl_task_failed": 0,
            "etl_last_run_timestamp": 0,
            "etl_last_run_duration_seconds": 0,
            "etl_table_count": {"ods": 0, "dwd": 0, "dws": 0, "ads": 0},
            "etl_rows_processed_total": 0,
            "mysql_connection_status": 0,
            "minio_connection_status": 0,
            "kafka_messages_total": 0,
            "data_freshness_seconds": 0,
        }
        self._update_metrics()

    def _update_metrics(self):
        """更新指标数据"""
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # 统计各层表数量
            for tier in ['ods', 'dwd', 'dws', 'ads']:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = '{MYSQL_DATABASE}'
                    AND table_name LIKE '{tier}_%'
                """)
                self.metrics["etl_table_count"][tier] = cursor.fetchone()[0]

            # 统计总行数
            total_rows = 0
            for tier in ['ods', 'dwd', 'dws', 'ads']:
                cursor.execute(f"""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = '{MYSQL_DATABASE}'
                    AND table_name LIKE '{tier}_%'
                """)
                tables = cursor.fetchall()
                for (table_name,) in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        total_rows += cursor.fetchone()[0]
                    except:
                        pass
            self.metrics["etl_rows_processed_total"] = total_rows

            # 检查 MySQL 连接
            self.metrics["mysql_connection_status"] = 1

            conn.close()
        except Exception as e:
            self.metrics["mysql_connection_status"] = 0
            print(f"MySQL 连接失败: {e}")

    def refresh(self):
        """刷新指标"""
        self._update_metrics()
        self.metrics["etl_last_run_timestamp"] = time.time()


class MetricsHandler(BaseHTTPRequestHandler):
    """Prometheus 指标 HTTP Handler"""

    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()

            collector = MetricsCollector()
            lines = []

            # ETL 任务指标
            lines.append("# HELP etl_task_total ETL 任务总数")
            lines.append("# TYPE etl_task_total gauge")
            lines.append(f"etl_task_total {collector.metrics['etl_task_total']}")

            lines.append("# HELP etl_task_success ETL 任务成功数")
            lines.append("# TYPE etl_task_success gauge")
            lines.append(f"etl_task_success {collector.metrics['etl_task_success']}")

            lines.append("# HELP etl_task_failed ETL 任务失败数")
            lines.append("# TYPE etl_task_failed gauge")
            lines.append(f"etl_task_failed {collector.metrics['etl_task_failed']}")

            lines.append("# HELP etl_last_run_timestamp 上次 ETL 运行时间戳")
            lines.append("# TYPE etl_last_run_timestamp gauge")
            lines.append(f"etl_last_run_timestamp {collector.metrics['etl_last_run_timestamp']}")

            lines.append("# HELP etl_last_run_duration_seconds 上次 ETL 运行耗时")
            lines.append("# TYPE etl_last_run_duration_seconds gauge")
            lines.append(f"etl_last_run_duration_seconds {collector.metrics['etl_last_run_duration_seconds']}")

            lines.append("# HELP etl_rows_processed_total ETL 处理总行数")
            lines.append("# TYPE etl_rows_processed_total counter")
            lines.append(f"etl_rows_processed_total {collector.metrics['etl_rows_processed_total']}")

            # 各层表数量
            for layer, count in collector.metrics["etl_table_count"].items():
                lines.append(f'etl_table_count{{layer="{layer}"}} {count}')

            # 连接状态
            lines.append("# HELP mysql_connection_status MySQL 连接状态 (1=正常)")
            lines.append("# TYPE mysql_connection_status gauge")
            lines.append(f"mysql_connection_status {collector.metrics['mysql_connection_status']}")

            lines.append("# HELP minio_connection_status MinIO 连接状态 (1=正常)")
            lines.append("# TYPE minio_connection_status gauge")
            lines.append(f"minio_connection_status {collector.metrics['minio_connection_status']}")

            lines.append("# HELP kafka_messages_total Kafka 消息总数")
            lines.append("# TYPE kafka_messages_total counter")
            lines.append(f"kafka_messages_total {collector.metrics['kafka_messages_total']}")

            self.wfile.write("\n".join(lines).encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志


def main():
    print("=" * 60)
    print("  ETL 指标导出器 - Prometheus Exporter")
    print(f"  端口: {METRICS_PORT}")
    print(f"  指标地址: http://localhost:{METRICS_PORT}/metrics")
    print(f"  健康检查: http://localhost:{METRICS_PORT}/health")
    print("=" * 60)

    server = HTTPServer(("0.0.0.0", METRICS_PORT), MetricsHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n指标导出器已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
