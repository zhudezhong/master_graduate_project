import json
from typing import Any

from app.core.config import Settings

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
        self._memory_queue: list[dict[str, Any]] = []
        self._init_clients()

    def _init_clients(self) -> None:
        if self.settings.use_mock_queue or Producer is None:
            return
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
        except Exception:
            self._producer = None
            self._consumer = None

    def publish_product(self, payload: dict[str, Any]) -> None:
        if self._producer is None:
            self._memory_queue.append(payload)
            return
        self._producer.produce(self.settings.kafka_product_topic, json.dumps(payload).encode("utf-8"))
        self._producer.flush()

    def drain_mock_messages(self) -> list[dict[str, Any]]:
        rows = list(self._memory_queue)
        self._memory_queue.clear()
        return rows

    def consume_products(self, max_messages: int, timeout_seconds: float = 5.0) -> list[dict[str, Any]]:
        if max_messages <= 0:
            return []

        if self._consumer is None:
            rows = self._memory_queue[:max_messages]
            self._memory_queue = self._memory_queue[max_messages:]
            return rows

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
