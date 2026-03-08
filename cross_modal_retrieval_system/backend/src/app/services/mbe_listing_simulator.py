import hashlib
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List

try:
    from app.core.config import Settings, settings
    from app.infra.category_taxonomy_repo import taxonomy_repo, CategoryTaxonomyRepository
    from app.infra.kafka_client import ProductQueue, get_product_queue_singleton
    from app.schemas.ingest import ProductIngestRecord
except ModuleNotFoundError:
    # Allow running this file directly: python src/app/services/mbe_listing_simulator.py
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from app.core.config import Settings, settings
    from app.infra.category_taxonomy_repo import taxonomy_repo, CategoryTaxonomyRepository
    from app.infra.kafka_client import ProductQueue, get_product_queue_singleton
    from app.schemas.ingest import ProductIngestRecord

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MbeListingSimulator:
    def __init__(
        self,
        settings: Settings,
        queue: ProductQueue,
    ):
        self.settings = settings
        self.queue = queue
        self._stop_requested = False
        self._is_running = False

    def start(self) -> None:
        if not self.settings.mbe_stream_enabled:
            return
        if self._is_running:
            return

        self._stop_requested = False
        self._is_running = True
        logger.info("MBE listing simulator started.")
        try:
            self._run()
        finally:
            self._is_running = False
            logger.info("MBE listing simulator stopped.")

    def stop(self) -> None:
        self._stop_requested = True

    def _run(self) -> None:
        file_path = Path(self.settings.mbe_stream_data_path)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path

        if not file_path.exists():
            logger.warning("MBE stream file not found: %s", file_path)
            return

        total_sent = 0
        batch_size = self.settings.mbe_stream_batch_size
        interval = self.settings.mbe_stream_interval_seconds
        max_records = self.settings.mbe_stream_max_records

        while not self._stop_requested:
            batch: List[ProductIngestRecord] = []
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if self._stop_requested:
                        break

                    row = line.strip()
                    if not row:
                        continue

                    try:
                        data = json.loads(row)
                        batch.append(self._to_ingest_record(data))
                    except Exception as exc:
                        logger.debug("skip malformed MBE row: %s", exc)
                        continue

                    if len(batch) >= batch_size:
                        self._flush(batch)
                        total_sent += len(batch)
                        logger.info("MBE simulator pushed batch=%s total=%s", len(batch), total_sent)
                        batch.clear()

                        if max_records > 0 and total_sent >= max_records:
                            logger.info("MBE simulator reached max records: %s", max_records)
                            return

                        if interval > 0:
                            time.sleep(interval)

                if batch and not self._stop_requested:
                    self._flush(batch)
                    total_sent += len(batch)
                    logger.info("MBE simulator pushed batch=%s total=%s", len(batch), total_sent)

                    if max_records > 0 and total_sent >= max_records:
                        logger.info("MBE simulator reached max records: %s", max_records)
                        return

            if not self.settings.mbe_stream_loop:
                break

        logger.info("MBE simulator exited with total pushed=%s", total_sent)

    def _flush(self, products: List[ProductIngestRecord]) -> None:
        if not products:
            return
        try:
            # In the streaming ingress layer, flush only publishes "new listing" events to Kafka.
            for product in products:
                self.queue.publish_product(product.model_dump())
        except Exception as exc:
            logger.exception("MBE simulator kafka publish failed: %s", exc)

    def _to_ingest_record(self, data: Dict[str, object]) -> ProductIngestRecord:
        product_id = MbeListingSimulator._to_product_id(str(data.get("id", "")))
        title = str(data.get("doc_title", "")).strip()
        image_url = str(data.get("doc_image", "")).strip()

        # MBE category hierarchy:
        # doc_industry_name is the top-level super-category (single label for SCPH),
        # and doc_cate1_name ~ doc_cate4_name are finer sub-categories (multi-label for MIH).
        cate1 = str(data.get("doc_cate1_name", "")).strip()
        cate2 = str(data.get("doc_cate2_name", "")).strip()
        cate3 = str(data.get("doc_cate3_name", "")).strip()
        cate4 = str(data.get("doc_cate4_name", "")).strip()
        industry = str(data.get("doc_industry_name", "")).strip() or "UNKNOWN"
        attributes_raw = str(data.get("doc_attributes", "")).strip()

        description_parts = [x for x in (industry, cate1, cate2, cate3, cate4, attributes_raw) if x]
        description = " | ".join(description_parts)

        # Query category ids from taxonomy tables first; insert new categories when missing.
        industry_id = taxonomy_repo.get_or_create_super_category(industry)
        category_tokens = [x for x in (cate1, cate2, cate3, cate4) if x]
        category_ids: list[int] = []
        for token in category_tokens:
            cid = taxonomy_repo.get_or_create_sub_category(
                name=token,
                super_category_id=industry_id,
            )
            if cid not in category_ids:
                category_ids.append(cid)

        attributes = MbeListingSimulator._parse_attributes(attributes_raw)

        return ProductIngestRecord(
            product_id=product_id,
            image_url=image_url,  # train data
            title=title,  # train data
            description=description,
            category_ids=category_ids, # train label for MIH
            industry_id=industry_id, # train label for SCPH
            timestamp=int(time.time()),
            attributes=attributes,
        )

    @staticmethod
    def _to_product_id(raw_id: str) -> int:
        raw_id = raw_id.strip()
        if not raw_id:
            return int(time.time() * 1000)
        try:
            return int(raw_id, 16) % 2147483647
        except ValueError:
            return MbeListingSimulator._stable_int(raw_id)

    @staticmethod
    def _stable_int(text: str) -> int:
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    @staticmethod
    def _parse_attributes(raw: str) -> Dict[str, str]:
        attrs: Dict[str, str] = {}
        if not raw:
            return attrs

        for pair in raw.split(",,"):
            part = pair.strip()
            if not part:
                continue
            if ":" in part:
                key, value = part.split(":", 1)
                attrs[key.strip()] = value.replace("!!!", "|").strip()
            else:
                attrs[part] = ""
        return attrs

if __name__ == "__main__":
    if settings.kafka_bootstrap_servers.startswith("kafka:"):
        logger.warning(
            "detected docker-internal kafka host '%s' in standalone mode, fallback to 127.0.0.1:9092",
            settings.kafka_bootstrap_servers,
        )
        settings.kafka_bootstrap_servers = "127.0.0.1:9092"

    queue = get_product_queue_singleton()
    simulator = MbeListingSimulator(
        settings=settings,
        queue=queue,
    )

    def _handle_signal(signum: int, _frame: object) -> None:
        logger.info("received signal=%s, stopping MBE simulator...", signum)
        simulator.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("starting MBE listing simulator in standalone mode...")
    simulator.start()