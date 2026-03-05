from dataclasses import dataclass
from typing import Any

from app.core.config import Settings

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
        self._scph_collection: Collection | None = None
        self._mih_collection: Collection | None = None
        self._memory_scph: dict[int, IndexRecord] = {}
        self._memory_mih: dict[int, IndexRecord] = {}
        self._init_client()

    def _init_client(self) -> None:
        if connections is None or Collection is None:
            raise RuntimeError("pymilvus is not installed; index storage layer cannot run.")
        try:
            connections.connect(
                alias=self._alias,
                uri=self.settings.milvus_uri,
                token=self.settings.milvus_token or None,
                db_name=self.settings.milvus_db_name,
            )
            self._scph_collection = self._ensure_collection(self.settings.milvus_collection_scph)
            self._mih_collection = self._ensure_collection(self.settings.milvus_collection_mih)
            self._scph_collection.load()
            self._mih_collection.load()
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to connect/initialize Milvus: {exc}") from exc

    def _ensure_collection(self, name: str) -> Collection:
        assert utility is not None and FieldSchema is not None and CollectionSchema is not None and DataType is not None
        if utility.has_collection(name, using=self._alias):
            return Collection(name=name, using=self._alias)

        fields = [
            FieldSchema(name="product_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
            FieldSchema(name="hash_code", dtype=DataType.BINARY_VECTOR, dim=self.settings.hash_bits),
            FieldSchema(name="category_id", dtype=DataType.INT64),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="ts", dtype=DataType.INT64),
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

    @staticmethod
    def _first_category(category_ids: list[int]) -> int:
        return category_ids[0] if category_ids else -1

    @staticmethod
    def _filter_category(rec: IndexRecord, category_filter: list[int]) -> bool:
        if not category_filter:
            return True
        return any(c in rec.category_ids for c in category_filter)

    def upsert_scph(self, record: IndexRecord) -> None:
        assert self._scph_collection is not None
        data = [
            [record.product_id],
            [self._to_binary_bytes(record.code)],
            [self._first_category(record.category_ids)],
            [str(record.payload.get("title", ""))],
            [str(record.payload.get("description", ""))],
            [int(record.payload.get("timestamp", 0))],
        ]
        self._scph_collection.upsert(data)
        self._scph_collection.flush()
        self._memory_scph[record.product_id] = record

    def upsert_mih(self, record: IndexRecord) -> None:
        assert self._mih_collection is not None
        data = [
            [record.product_id],
            [self._to_binary_bytes(record.code)],
            [self._first_category(record.category_ids)],
            [str(record.payload.get("title", ""))],
            [str(record.payload.get("description", ""))],
            [int(record.payload.get("indexed_at", 0))],
        ]
        self._mih_collection.upsert(data)
        self._mih_collection.flush()
        self._memory_mih[record.product_id] = record

    def get_product(self, product_id: int) -> IndexRecord | None:
        return self._memory_scph.get(product_id)

    def search_scph(self, code: list[int], top_k: int, category_filter: list[int]) -> list[tuple[IndexRecord, float]]:
        assert self._scph_collection is not None
        expr = ""
        if category_filter:
            expr = f"category_id in {category_filter}"
        hits = self._scph_collection.search(
            data=[self._to_binary_bytes(code)],
            anns_field="hash_code",
            param={"metric_type": "HAMMING", "params": {"nprobe": 16}},
            limit=top_k,
            expr=expr,
            output_fields=["product_id", "category_id", "title", "description", "ts"],
        )[0]
        rows: list[tuple[IndexRecord, float]] = []
        for hit in hits:
            pid = int(hit.id)
            rec = self._memory_scph.get(pid)
            if rec is None:
                entity = hit.entity
                rec = IndexRecord(
                    product_id=pid,
                    code=[],
                    category_ids=[int(entity.get("category_id", -1))],
                    payload={
                        "title": entity.get("title", ""),
                        "description": entity.get("description", ""),
                        "timestamp": int(entity.get("ts", 0)),
                    },
                )
            rows.append((rec, float(hit.distance)))
        return rows

    def search_mih_by_ids(self, product_ids: list[int], distances: list[float]) -> list[tuple[IndexRecord, float]]:
        assert self._mih_collection is not None
        if not product_ids:
            return []
        expr = f"product_id in {product_ids}"
        rows = self._mih_collection.query(
            expr=expr,
            output_fields=["product_id", "category_id", "title", "description", "ts"],
        )
        from_milvus: dict[int, IndexRecord] = {}
        for row in rows:
            pid = int(row["product_id"])
            from_milvus[pid] = IndexRecord(
                product_id=pid,
                code=[],
                category_ids=[int(row.get("category_id", -1))],
                payload={
                    "title": str(row.get("title", "")),
                    "description": str(row.get("description", "")),
                    "indexed_at": int(row.get("ts", 0)),
                },
            )

        out: list[tuple[IndexRecord, float]] = []
        for pid, dist in zip(product_ids, distances):
            rec = self._memory_mih.get(pid) or from_milvus.get(pid)
            if rec is not None:
                out.append((rec, dist))
        return out
