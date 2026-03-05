from functools import lru_cache
from typing import Literal

from pydantic import Field
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
    milvus_collection_scph: str = "scph_items"
    milvus_collection_mih: str = "mih_items"
    milvus_partition_name: str = "p_default"
    milvus_consistency: Literal["Strong", "Session", "Bounded", "Eventually"] = "Bounded"

    kafka_bootstrap_servers: str = "127.0.0.1:9092"
    kafka_product_topic: str = "product_ingest"
    kafka_consumer_group: str = "retrieval_system"

    hash_bits: int = 64
    topk_default: int = 20
    feature_dim_image: int = 512
    feature_dim_text: int = 768

    use_mock_feature_extractor: bool = False
    use_mock_queue: bool = True

    request_timeout_seconds: int = Field(default=30, ge=1, le=300)

    device: str = "cpu"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"


@lru_cache
def get_settings() -> Settings:
    return Settings()
