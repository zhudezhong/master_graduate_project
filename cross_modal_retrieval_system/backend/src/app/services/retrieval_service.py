import time

from app.infra.catalog import ProductCatalog
from app.infra.milvus_client import MilvusRepository
from app.schemas.common import RetrievalItem, RetrievalResponse
from app.services.feature_service import FeatureService
from app.services.hash_service import HashEngineService


class RetrievalService:
    def __init__(
        self,
        catalog: ProductCatalog,
        feature_service: FeatureService,
        hash_service: HashEngineService,
        milvus_repo: MilvusRepository,
    ):
        self.catalog = catalog
        self.feature_service = feature_service
        self.hash_service = hash_service
        self.milvus_repo = milvus_repo

    def similar_by_product(self, product_id: int, top_k: int, category_filter: list[int]) -> RetrievalResponse:
        start = time.perf_counter()
        product = self.catalog.get(product_id)
        if product is None:
            raise ValueError(f"product_id {product_id} not found")
        image_feat, _ = self.feature_service.product_features(product)
        code = self.hash_service.encode_image_scph(image_feat)
        rows = self.milvus_repo.search_scph(code, top_k=top_k, category_filter=category_filter)
        results = [RetrievalItem(product_id=r.product_id, score=dist, payload=r.payload) for r, dist in rows]
        return RetrievalResponse(latency_ms=int((time.perf_counter() - start) * 1000), results=results)

    def similar_by_uploaded_image(
        self,
        image_bytes: bytes,
        filename: str,
        top_k: int,
        category_filter: list[int],
    ) -> RetrievalResponse:
        start = time.perf_counter()
        image_feat = self.feature_service.image_from_bytes(image_bytes, filename=filename)
        code = self.hash_service.encode_image_scph(image_feat)
        rows = self.milvus_repo.search_scph(code, top_k=top_k, category_filter=category_filter)
        results = [RetrievalItem(product_id=r.product_id, score=dist, payload=r.payload) for r, dist in rows]
        return RetrievalResponse(latency_ms=int((time.perf_counter() - start) * 1000), results=results)

    def text_to_image(self, query_text: str, top_k: int) -> RetrievalResponse:
        start = time.perf_counter()
        text_feat = self.feature_service.text_from_query(query_text)
        res = self.hash_service.encode_mih_query(text_feat, modality="text", topk=top_k)
        ids = res["ids"][0].tolist()
        distances = [float(x) for x in res["distances"][0].tolist()]
        rows = self.milvus_repo.search_mih_by_ids(ids, distances)
        results = [RetrievalItem(product_id=r.product_id, score=dist, payload=r.payload) for r, dist in rows]
        return RetrievalResponse(latency_ms=int((time.perf_counter() - start) * 1000), results=results)

    def image_to_image_cross(self, image_url: str, top_k: int) -> RetrievalResponse:
        start = time.perf_counter()
        image_feat = self.feature_service.image_from_url(image_url)
        res = self.hash_service.encode_mih_query(image_feat, modality="image", topk=top_k)
        ids = res["ids"][0].tolist()
        distances = [float(x) for x in res["distances"][0].tolist()]
        rows = self.milvus_repo.search_mih_by_ids(ids, distances)
        results = [RetrievalItem(product_id=r.product_id, score=dist, payload=r.payload) for r, dist in rows]
        return RetrievalResponse(latency_ms=int((time.perf_counter() - start) * 1000), results=results)
