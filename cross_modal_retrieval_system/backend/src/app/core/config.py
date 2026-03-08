from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import torch


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cross Modal Retrieval API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    milvus_uri: str = "http://127.0.0.1:19530"
    milvus_token: str = ""
    milvus_db_name: str = "default"
    milvus_collection_products: str = Field(
        default="scph_items",
        validation_alias=AliasChoices("MILVUS_COLLECTION_PRODUCTS", "MILVUS_COLLECTION_SCPH"),
    )
    milvus_collection_mih: str = "mih_items"
    milvus_partition_name: str = "p_default"
    milvus_consistency: Literal["Strong", "Session", "Bounded", "Eventually"] = "Bounded"
    milvus_connect_retries: int = Field(default=30, ge=1, le=300)
    milvus_connect_retry_interval_seconds: float = Field(default=2.0, ge=0.1, le=30.0)

    kafka_bootstrap_servers: str = "127.0.0.1:29092"
    kafka_product_topic: str = "product_ingest"
    kafka_consumer_group: str = "retrieval_system"
    ingest_consume_enabled: bool = True
    ingest_consume_max_messages: int = Field(default=100, ge=1, le=100000)
    ingest_consume_timeout_seconds: float = Field(default=10.0, ge=0.1, le=300.0)
    ingest_consume_interval_seconds: float = Field(default=300.0, ge=1.0, le=86400.0)

    hash_bits: int = 64
    topk_default: int = 40
    feature_dim_image: int = 512
    feature_dim_text: int = 768
    text_model_name: str = "shibing624/text2vec-base-chinese"

    use_mock_feature_extractor: bool = False

    category_taxonomy_db_path: str = "data/category_taxonomy.db"

    mbe_stream_enabled: bool = True
    mbe_stream_data_path: str = "data/MBE_test.shuffled.jsonl"
    mbe_stream_batch_size: int = 1024
    mbe_stream_interval_seconds: float = 20
    mbe_stream_max_records: int = 20000
    mbe_stream_loop: bool = False

    request_timeout_seconds: int = Field(default=30, ge=1, le=300)

    device: str = "cpu"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    
settings = Settings()