import time

import torch

from app.infra.catalog import ProductCatalog
from app.infra.kafka_client import ProductQueue
from app.infra.milvus_client import IndexRecord, MilvusRepository
from app.schemas.ingest import ProductIngestRecord
from app.services.feature_service import FeatureService
from app.services.hash_service import HashEngineService, pm1_to_binary_vector


class IngestService:
    def __init__(
        self,
        queue: ProductQueue,
        catalog: ProductCatalog,
        feature_service: FeatureService,
        hash_service: HashEngineService,
        milvus_repo: MilvusRepository,
    ):
        self.queue = queue
        self.catalog = catalog
        self.feature_service = feature_service
        self.hash_service = hash_service
        self.milvus_repo = milvus_repo

    def ingest_products(self, products: list[ProductIngestRecord]) -> dict[str, int]:
        for product in products:
            self.queue.publish_product(product.model_dump())
            self.catalog.upsert(product)
        self._train_and_index(products)
        return {"accepted": len(products), "queued": len(products)}

    def replay_from_queue(self, max_messages: int, timeout_seconds: float) -> dict[str, int]:
        raw_messages = self.queue.consume_products(max_messages=max_messages, timeout_seconds=timeout_seconds)
        products: list[ProductIngestRecord] = []
        for row in raw_messages:
            try:
                product = ProductIngestRecord.model_validate(row)
            except Exception:
                continue
            self.catalog.upsert(product)
            products.append(product)

        self._train_and_index(products)
        return {
            "consumed": len(raw_messages),
            "validated": len(products),
            "indexed": len(products),
        }

    def _train_and_index(self, products: list[ProductIngestRecord]) -> None:
        if not products:
            return
        image_feats = []
        text_feats = []
        labels = []
        ids = []
        for p in products:
            image_feat, text_feat = self.feature_service.product_features(p)
            image_feats.append(image_feat)
            text_feats.append(text_feat)
            labels.append(p.category_ids[0] if p.category_ids else 0)
            ids.append(p.product_id)

        x_img = torch.stack(image_feats, dim=0)
        x_txt = torch.stack(text_feats, dim=0)
        y = torch.tensor(labels, dtype=torch.long)
        pid = torch.tensor(ids, dtype=torch.long)

        self.hash_service.update_scph(x_img, y)
        self.hash_service.update_mih(x_img, x_txt, y, pid)

        for i, p in enumerate(products):
            scph_code = self.hash_service.encode_image_scph(x_img[i])
            self.milvus_repo.upsert_scph(
                IndexRecord(
                    product_id=p.product_id,
                    code=scph_code,
                    category_ids=p.category_ids,
                    payload={
                        "title": p.title,
                        "description": p.description,
                        "timestamp": p.timestamp,
                    },
                )
            )
            mih_code = pm1_to_binary_vector(self.hash_service.mih._db_codes_pm1[-len(products) + i])  # noqa: SLF001
            self.milvus_repo.upsert_mih(
                IndexRecord(
                    product_id=p.product_id,
                    code=mih_code,
                    category_ids=p.category_ids,
                    payload={
                        "title": p.title,
                        "description": p.description,
                        "indexed_at": int(time.time()),
                    },
                )
            )
