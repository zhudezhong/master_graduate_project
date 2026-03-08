import time

import torch

from app.infra.catalog import ProductCatalog
from app.infra.kafka_client import ProductQueue, get_product_queue_singleton
from app.infra.milvus_client import MilvusRepository, get_milvus_repo_singleton
from app.schemas.ingest import ProductIngestRecord
from app.services.feature_service import FeatureService, get_feature_service_singleton
from app.services.hash_service import HashEngineService, get_hash_engine_singleton, pm1_to_binary_vector


class IngestService:
    def __init__(
        self,
        queue: ProductQueue,
        feature_service: FeatureService,
        hash_service: HashEngineService,
        milvus_repo: MilvusRepository,
        catalog: ProductCatalog | None = None,
    ):
        self.queue = queue
        self.feature_service = feature_service
        self.hash_service = hash_service
        self.milvus_repo = milvus_repo
        self.catalog = catalog

    def ingest_products(self, products: list[ProductIngestRecord]) -> dict[str, int]:
        accepted = 0
        queued = 0
        for product in products:
            accepted += 1
            if self.catalog is not None:
                self.catalog.upsert(product)
            self.queue.publish_product(product.model_dump())
            queued += 1
        return {"accepted": accepted, "queued": queued}

    def replay_from_queue(self, max_messages: int, timeout_seconds: float) -> dict[str, int]:
        products = self.consume_products_and_train_hash_model(
            max_messages=max_messages,
            timeout_seconds=timeout_seconds,
        )
        count = len(products)
        return {"consumed": count, "validated": count, "indexed": count}

    def consume_products_and_train_hash_model(self, max_messages: int, timeout_seconds: float) -> list[ProductIngestRecord]:
        """消费kafka中的商品数据，提取特征并写入milvus索引"""
        raw_messages = self.queue.consume_products(max_messages=max_messages, timeout_seconds=timeout_seconds)
        products: list[ProductIngestRecord] = []
        for row in raw_messages:
            try:
                product = ProductIngestRecord.model_validate(row)
            except Exception:
                continue
            products.append(product)

        self._index_products(products)
        return products

    def _index_products(self, products: list[ProductIngestRecord]) -> None:
        if not products:
            return

        image_feats: list[torch.Tensor] = []
        text_feats: list[torch.Tensor] = []
        scph_labels: list[int] = []
        ids: list[int] = []

        # 提取商品的图像特征、文本特征，将商品数据插入milvus中
        for product in products:
            image_feat, text_feat = self.feature_service.product_features(product)
            image_feats.append(image_feat)
            text_feats.append(text_feat)
            top_label = product.industry_id
            if top_label is None:
                top_label = product.category_ids[0] if product.category_ids else -1
            scph_labels.append(top_label)
            ids.append(product.product_id)
            if self.catalog is not None:
                self.catalog.upsert(product)

        x_img = torch.stack(image_feats, dim=0)
        x_txt = torch.stack(text_feats, dim=0)
        y_scph = torch.tensor(scph_labels, dtype=torch.long)
        y_mih = self._build_mih_label_matrix(products)
        pid = torch.tensor(ids, dtype=torch.long)

        # 更新哈希模型
        self.hash_service.update_scph(x_img, y_scph)
        self.hash_service.update_mih(x_img, x_txt, y_mih, pid)

        for i, product in enumerate(products):
            scph_code = self.hash_service.encode_image_scph(x_img[i])
            mih_code = pm1_to_binary_vector(self.hash_service.mih._db_codes_pm1[-len(products) + i])  # noqa: SLF001
            payload = {
                "title": product.title,
                "description": product.description,
                "image_url": product.image_url,
                "attributes": product.attributes,
                "category_ids": product.category_ids,
                "industry_id": product.industry_id,
                "timestamp": product.timestamp,
                "indexed_at": int(time.time()),
                "image_feature": x_img[i].tolist(),
                "text_feature": x_txt[i].tolist(),
                "scph_code": scph_code,
                "mih_code": mih_code,
            }
            # Unified single-product record in Milvus with full payload and both hash codes.
            self.milvus_repo.upsert_product_record(
                product_id=product.product_id,
                payload=payload,
            )

    @staticmethod
    def _build_mih_label_matrix(products: list[ProductIngestRecord]) -> torch.Tensor:
        category_vocab: dict[int, int] = {}
        for product in products:
            for category_id in product.category_ids:
                if category_id not in category_vocab:
                    category_vocab[category_id] = len(category_vocab)

        if not category_vocab:
            return torch.ones((len(products), 1), dtype=torch.float32)

        label_mat = torch.zeros((len(products), len(category_vocab)), dtype=torch.float32)
        for row_idx, product in enumerate(products):
            if product.category_ids:
                for category_id in product.category_ids:
                    label_mat[row_idx, category_vocab[category_id]] = 1.0
            else:
                label_mat[row_idx, 0] = 1.0
        return label_mat

if __name__ == "__main__":
    ingest = IngestService(
        queue=get_product_queue_singleton(),
        feature_service=get_feature_service_singleton(),
        hash_service=get_hash_engine_singleton(),
        milvus_repo=get_milvus_repo_singleton(),
    )
    ingest.consume_products_and_train_hash_model(max_messages=100, timeout_seconds=10)
    
