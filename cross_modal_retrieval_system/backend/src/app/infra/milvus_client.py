from dataclasses import dataclass
import json
import time
from typing import Any

from app.core.config import Settings, settings

try:
    from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
except Exception:  # pragma: no cover
    Collection = None  # type: ignore[assignment]
    CollectionSchema = None  # type: ignore[assignment]
    DataType = None  # type: ignore[assignment]
    FieldSchema = None  # type: ignore[assignment]
    connections = None  # type: ignore[assignment]
    utility = None  # type: ignore[assignment]


@dataclass
class IndexRecord:
    product_id: int
    code: list[int]
    category_ids: list[int]
    payload: dict[str, Any]


class MilvusRepository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._alias = "default"
        self._product_collection: Collection | None = None
        self._memory_products: dict[int, IndexRecord] = {}
        self._init_client()

    def _init_client(self) -> None:
        if connections is None or Collection is None:
            raise RuntimeError("pymilvus is not installed; index storage layer cannot run.")
        last_exc: Exception | None = None
        for attempt in range(1, self.settings.milvus_connect_retries + 1):
            try:
                connections.connect(
                    alias=self._alias,
                    uri=self.settings.milvus_uri,
                    token=self.settings.milvus_token or None,
                    db_name=self.settings.milvus_db_name,
                )
                self._product_collection = self._ensure_collection(self.settings.milvus_collection_products)
                self._product_collection.load()
                return
            except Exception as exc:  # pragma: no cover
                last_exc = exc
                if attempt < self.settings.milvus_connect_retries:
                    time.sleep(self.settings.milvus_connect_retry_interval_seconds)

        assert last_exc is not None
        raise RuntimeError(
            f"Failed to connect/initialize Milvus after {self.settings.milvus_connect_retries} attempts: {last_exc}"
        ) from last_exc

    def _ensure_collection(self, name: str) -> Collection:
        assert utility is not None and FieldSchema is not None and CollectionSchema is not None and DataType is not None
        if utility.has_collection(name, using=self._alias):
            # The project now uses a unified latest schema only.
            # Old data is intentionally discarded on startup.
            utility.drop_collection(name, using=self._alias)

        fields = [
            FieldSchema(name="product_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
            FieldSchema(name="hash_code", dtype=DataType.BINARY_VECTOR, dim=self.settings.hash_bits),
            FieldSchema(name="category_id", dtype=DataType.INT64),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="ts", dtype=DataType.INT64),
            FieldSchema(name="payload_json", dtype=DataType.JSON),
        ]
        schema = CollectionSchema(fields=fields, description=f"{name} binary hash collection")
        collection = Collection(name=name, schema=schema, using=self._alias)
        collection.create_index(
            field_name="hash_code",
            index_params={
                "index_type": "BIN_IVF_FLAT",
                "metric_type": "HAMMING",
                "params": {"nlist": 128},
            },
        )
        return collection

    @staticmethod
    def _hamming(a: list[int], b: list[int]) -> int:
        return sum(1 for x, y in zip(a, b) if x != y)

    @staticmethod
    def _to_binary_bytes(bits: list[int]) -> bytes:
        n_bytes = (len(bits) + 7) // 8
        packed = bytearray(n_bytes)
        for i, bit in enumerate(bits):
            if bit:
                packed[i // 8] |= 1 << (7 - i % 8)
        return bytes(packed)

    def _from_binary_bytes(self, raw: bytes | bytearray | memoryview) -> list[int]:
        data = bytes(raw)
        out: list[int] = []
        for i in range(self.settings.hash_bits):
            b = data[i // 8]
            out.append((b >> (7 - (i % 8))) & 1)
        return out

    @staticmethod
    def _first_category(category_ids: list[int]) -> int:
        return category_ids[0] if category_ids else -1

    @staticmethod
    def _filter_category(rec: IndexRecord, category_filter: list[int]) -> bool:
        if not category_filter:
            return True
        return any(c in rec.category_ids for c in category_filter)

    def upsert_product_record(self, product_id: int, payload: dict[str, Any]) -> None:
        """Use product_id as primary key and payload as canonical product schema."""
        assert self._product_collection is not None
        scph_code = [int(x) for x in payload.get("scph_code", [])]
        if not scph_code:
            raise ValueError("payload.scph_code is required for Milvus binary index.")
        category_ids = [int(x) for x in payload.get("category_ids", [])]
        data = [
            [product_id],
            [self._to_binary_bytes(scph_code)],
            [self._first_category(category_ids)],
            [str(payload.get("title", ""))],
            [str(payload.get("description", ""))[:8192]],
            [int(payload.get("timestamp", 0))],
            [payload],
        ]
        self._product_collection.upsert(data)
        self._product_collection.flush()
        self._memory_products[product_id] = IndexRecord(
            product_id=product_id,
            code=scph_code,
            category_ids=category_ids,
            payload=payload,
        )

    def upsert_scph(self, record: IndexRecord) -> None:
        # Backward compatibility alias: callers can still use old method name.
        payload = dict(record.payload)
        payload.setdefault("scph_code", record.code)
        payload.setdefault("category_ids", record.category_ids)
        self.upsert_product_record(product_id=record.product_id, payload=payload)


    def get_product(self, product_id: int) -> IndexRecord | None:
        in_memory = self._memory_products.get(product_id)
        if in_memory is not None:
            return in_memory

        assert self._product_collection is not None
        rows = self._product_collection.query(
            expr=f"product_id == {product_id}",
            output_fields=["product_id", "hash_code", "category_id", "title", "description", "ts", "payload_json"],
            limit=1,
        )
        if not rows:
            return None

        row = rows[0]
        raw_code = row.get("hash_code", b"")
        code: list[int] = []
        if isinstance(raw_code, (bytes, bytearray, memoryview)):
            code = self._from_binary_bytes(raw_code)

        payload_json = row.get("payload_json")
        payload: dict[str, Any]
        if isinstance(payload_json, dict):
            payload = payload_json
        elif isinstance(payload_json, str) and payload_json:
            try:
                payload = json.loads(payload_json)
            except Exception:
                payload = {}
        else:
            payload = {}

        if not payload:
            payload = {
                "title": str(row.get("title", "")),
                "description": str(row.get("description", "")),
                "timestamp": int(row.get("ts", 0)),
            }

        rec = IndexRecord(
            product_id=int(row["product_id"]),
            code=code,
            category_ids=[int(row.get("category_id", -1))],
            payload=payload,
        )
        self._memory_products[rec.product_id] = rec
        return rec

    def search_products_by_scph_code(self, code: list[int], top_k: int, category_filter: list[int]) -> list[tuple[IndexRecord, float]]:
        assert self._product_collection is not None
        expr = ""
        if category_filter:
            expr = f"category_id in {category_filter}"
        hits = self._product_collection.search(
            data=[self._to_binary_bytes(code)],
            anns_field="hash_code",
            param={"metric_type": "HAMMING", "params": {"nprobe": 16}},
            limit=top_k,
            expr=expr,
            output_fields=["product_id", "category_id", "title", "description", "ts", "payload_json"],
        )[0]
        rows: list[tuple[IndexRecord, float]] = []
        for hit in hits:
            pid = int(hit.id)
            rec = self._memory_products.get(pid)
            if rec is None:
                entity = hit.entity
                payload = entity.get("payload_json", {})
                if not isinstance(payload, dict):
                    payload = {
                        "title": entity.get("title", ""),
                        "description": entity.get("description", ""),
                        "timestamp": int(entity.get("ts", 0)),
                    }
                rec = IndexRecord(
                    product_id=pid,
                    code=[],
                    category_ids=[int(entity.get("category_id", -1))],
                    payload=payload,
                )
            rows.append((rec, float(hit.distance)))
        return rows

    def search_scph(self, code: list[int], top_k: int, category_filter: list[int]) -> list[tuple[IndexRecord, float]]:
        # Backward compatibility alias.
        return self.search_products_by_scph_code(code, top_k=top_k, category_filter=category_filter)

    def search_mih_by_ids(self, product_ids: list[int], distances: list[float]) -> list[tuple[IndexRecord, float]]:
        assert self._product_collection is not None
        if not product_ids:
            return []
        expr = f"product_id in {product_ids}"
        rows = self._product_collection.query(
            expr=expr,
            output_fields=["product_id", "category_id", "title", "description", "ts", "payload_json"],
        )
        from_milvus: dict[int, IndexRecord] = {}
        for row in rows:
            pid = int(row["product_id"])
            payload = row.get("payload_json", {})
            if not isinstance(payload, dict):
                payload = {
                    "title": str(row.get("title", "")),
                    "description": str(row.get("description", "")),
                    "indexed_at": int(row.get("ts", 0)),
                }
            from_milvus[pid] = IndexRecord(
                product_id=pid,
                code=[],
                category_ids=[int(row.get("category_id", -1))],
                payload=payload,
            )

        out: list[tuple[IndexRecord, float]] = []
        for pid, dist in zip(product_ids, distances):
            rec = self._memory_products.get(pid) or from_milvus.get(pid)
            if rec is not None:
                out.append((rec, dist))
        return out

    def list_products(self, limit: int) -> list[IndexRecord]:
        assert self._product_collection is not None
        if limit <= 0:
            return []
        rows = self._product_collection.query(
            expr="product_id >= 0",
            output_fields=["product_id", "hash_code", "category_id", "title", "description", "ts", "payload_json"],
            limit=limit,
        )
        out: list[IndexRecord] = []
        for row in rows:
            pid = int(row["product_id"])
            payload = row.get("payload_json", {})
            if isinstance(payload, str) and payload:
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            if not isinstance(payload, dict):
                payload = {}
            if not payload:
                payload = {
                    "title": str(row.get("title", "")),
                    "description": str(row.get("description", "")),
                    "timestamp": int(row.get("ts", 0)),
                }
            raw_code = row.get("hash_code", b"")
            code: list[int] = []
            if isinstance(raw_code, (bytes, bytearray, memoryview)):
                code = self._from_binary_bytes(raw_code)
            rec = IndexRecord(
                product_id=pid,
                code=code,
                category_ids=[int(row.get("category_id", -1))],
                payload=payload,
            )
            self._memory_products[pid] = rec
            out.append(rec)
        return out


_milvus_repo_singleton: MilvusRepository | None = None


def get_milvus_repo_singleton() -> MilvusRepository:
    global _milvus_repo_singleton
    if _milvus_repo_singleton is None:
        _milvus_repo_singleton = MilvusRepository(settings)
    return _milvus_repo_singleton
