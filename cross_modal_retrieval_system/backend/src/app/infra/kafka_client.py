import json
from typing import Any

from app.core.config import Settings, settings

try:
    from confluent_kafka import Consumer, Producer
except Exception:  # pragma: no cover
    Consumer = None  # type: ignore[assignment]
    Producer = None  # type: ignore[assignment]


class ProductQueue:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._producer = None
        self._consumer = None
        self._init_clients()

    def _init_clients(self) -> None:
        if Producer is None or Consumer is None:
            raise RuntimeError("confluent_kafka is required but not installed.")
        try:
            self._producer = Producer({"bootstrap.servers": self.settings.kafka_bootstrap_servers})
            self._consumer = Consumer(
                {
                    "bootstrap.servers": self.settings.kafka_bootstrap_servers,
                    "group.id": self.settings.kafka_consumer_group,
                    "auto.offset.reset": "earliest",
                }
            )
            self._consumer.subscribe([self.settings.kafka_product_topic])
        except Exception as exc:
            raise RuntimeError(f"failed to initialize Kafka clients: {exc}") from exc

    def publish_product(self, payload: dict[str, Any]) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer is not initialized.")
        self._producer.produce(self.settings.kafka_product_topic, json.dumps(payload).encode("utf-8"))
        self._producer.flush()

    def consume_products(self, max_messages: int, timeout_seconds: float = 5.0) -> list[dict[str, Any]]:
        if max_messages <= 0:
            return []

        if self._consumer is None:
            raise RuntimeError("Kafka consumer is not initialized.")

        messages: list[dict[str, Any]] = []
        idle_polls = 0
        max_idle_polls = max(1, int(timeout_seconds / 0.5))

        while len(messages) < max_messages and idle_polls < max_idle_polls:
            msg = self._consumer.poll(timeout=0.5)
            if msg is None:
                idle_polls += 1
                continue
            if msg.error():
                idle_polls += 1
                continue
            idle_polls = 0
            try:
                payload = json.loads(msg.value().decode("utf-8"))
                if isinstance(payload, dict):
                    messages.append(payload)
            except Exception:
                continue

        return messages


_product_queue_singleton: ProductQueue | None = None


def get_product_queue_singleton() -> ProductQueue:
    global _product_queue_singleton
    if _product_queue_singleton is None:
        _product_queue_singleton = ProductQueue(settings)
    return _product_queue_singleton
