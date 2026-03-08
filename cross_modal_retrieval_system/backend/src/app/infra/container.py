import logging
import threading
import time
from app.core.config import Settings
from app.infra.catalog import ProductCatalog
from app.infra.kafka_client import get_product_queue_singleton
from app.infra.milvus_client import get_milvus_repo_singleton
from app.services.feature_service import get_feature_service_singleton
from app.services.hash_service import get_hash_engine_singleton
from app.services.ingest_service import IngestService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class AppContainer:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.catalog = ProductCatalog()
        self.queue = get_product_queue_singleton()
        self.feature_service = get_feature_service_singleton()
        self.hash_service = get_hash_engine_singleton()
        self.milvus_repo = get_milvus_repo_singleton()

        self.ingest_service = IngestService(
            queue=self.queue,
            feature_service=self.feature_service,
            hash_service=self.hash_service,
            milvus_repo=self.milvus_repo,
            catalog=self.catalog,
        )
        self.retrieval_service = RetrievalService(
            catalog=self.catalog,
            feature_service=self.feature_service,
            hash_service=self.hash_service,
            milvus_repo=self.milvus_repo,
        )
        self._consume_stop_event = threading.Event()
        self._consume_thread: threading.Thread | None = None

    def start_background_jobs(self) -> None:
        if not self.settings.ingest_consume_enabled:
            logger.info("ingest consume job is disabled by config.")
            return
        if self._consume_thread is not None and self._consume_thread.is_alive():
            return

        self._consume_stop_event.clear()
        self._consume_thread = threading.Thread(
            target=self._consume_loop,
            name="ingest-consumer-loop",
            daemon=True,
        )
        self._consume_thread.start()
        logger.info(
            "started ingest consumer loop: every=%ss, max_messages=%s, poll_timeout=%ss",
            self.settings.ingest_consume_interval_seconds,
            self.settings.ingest_consume_max_messages,
            self.settings.ingest_consume_timeout_seconds,
        )

    def stop_background_jobs(self) -> None:
        self._consume_stop_event.set()
        if self._consume_thread is not None:
            self._consume_thread.join(timeout=10)
            self._consume_thread = None

    def _consume_loop(self) -> None:
        while not self._consume_stop_event.is_set():
            try:
                self.ingest_service.consume_products_and_train_hash_model(
                    max_messages=self.settings.ingest_consume_max_messages,
                    timeout_seconds=self.settings.ingest_consume_timeout_seconds,
                )
            except Exception as exc:
                logger.exception("ingest consumer loop iteration failed: %s", exc)

            self._consume_stop_event.wait(self.settings.ingest_consume_interval_seconds)
