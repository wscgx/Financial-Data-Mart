"""
Kafka 生产者 - 模拟实时交易数据流

用法:
    python kafka_producer.py [--topic financial_transactions] [--count 100] [--interval 1.0]
"""
import json
import time
import random
import argparse
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from configs.spark_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

PRODUCTS = [
    {"id": "P001", "name": "稳健理财A", "type": "fund", "risk": "low"},
    {"id": "P002", "name": "成长基金B", "type": "fund", "risk": "medium"},
    {"id": "P003", "name": "股票型基金C", "type": "fund", "risk": "high"},
    {"id": "P004", "name": "货币市场D", "type": "money_market", "risk": "low"},
    {"id": "P005", "name": "债券基金E", "type": "bond", "risk": "medium"},
    {"id": "P006", "name": "指数基金F", "type": "index", "risk": "medium"},
    {"id": "P007", "name": "混合基金G", "type": "hybrid", "risk": "medium"},
    {"id": "P008", "name": "QDII基金H", "type": "qdii", "risk": "high"},
]

BRANCHES = ["北京分行", "上海分行", "广州分行", "深圳分行", "杭州分行", "成都分行"]


def generate_transaction():
    """生成一条模拟交易记录"""
    product = random.choice(PRODUCTS)
    transaction_type = random.choice(["purchase", "redemption"])
    amount = round(random.uniform(1000, 500000), 2)
    price = round(random.uniform(0.8, 2.5), 4)
    quantity = round(amount / price, 4)

    return {
        "transaction_id": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}",
        "account_id": f"A{random.randint(1000, 9999)}",
        "customer_id": f"C{random.randint(100, 999)}",
        "product_id": product["id"],
        "product_name": product["name"],
        "product_type": product["type"],
        "risk_level": product["risk"],
        "transaction_type": transaction_type,
        "amount": amount,
        "price": price,
        "quantity": quantity,
        "fee": round(amount * random.uniform(0.001, 0.005), 2),
        "branch": random.choice(BRANCHES),
        "transaction_time": datetime.now().isoformat(),
        "status": "completed",
    }


def produce(topic, count, interval):
    """发送消息到 Kafka"""
    try:
        from confluent_kafka import Producer
    except ImportError:
        print("请先安装 confluent-kafka: pip install confluent-kafka")
        return

    conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "financial_producer",
    }
    producer = Producer(conf)

    def delivery_report(err, msg):
        if err is not None:
            print(f"消息发送失败: {err}")
        else:
            print(f"消息已发送: {msg.topic()}[{msg.partition()}] @ offset {msg.offset()}")

    print(f"开始向 Kafka topic '{topic}' 发送 {count} 条消息...")
    print(f"Kafka 服务器: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"发送间隔: {interval}s")
    print("-" * 60)

    for i in range(count):
        txn = generate_transaction()
        key = txn["account_id"]
        value = json.dumps(txn, ensure_ascii=False)

        producer.produce(topic, key=key, value=value, callback=delivery_report)
        producer.poll(0)

        if (i + 1) % 10 == 0:
            print(f"  已发送 {i+1}/{count} 条")

        time.sleep(interval)

    producer.flush()
    print("-" * 60)
    print(f"全部 {count} 条消息发送完成!")


def main():
    parser = argparse.ArgumentParser(description="Kafka 交易数据生产者")
    parser.add_argument("--topic", default=KAFKA_TOPIC, help="Kafka topic 名称")
    parser.add_argument("--count", type=int, default=100, help="发送消息数量")
    parser.add_argument("--interval", type=float, default=1.0, help="发送间隔(秒)")
    args = parser.parse_args()

    produce(args.topic, args.count, args.interval)


if __name__ == "__main__":
    main()
