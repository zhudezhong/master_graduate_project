import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from pymilvus import connections

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _milvus_available() -> bool:
    uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
    try:
        connections.connect(alias="test_api", uri=uri, timeout=2)
        connections.disconnect(alias="test_api")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _milvus_available(), reason="Milvus unavailable for API tests")


def _build_client() -> TestClient:
    from app.main import create_app

    return TestClient(create_app())


def test_ingest_then_similar_search() -> None:
    client = _build_client()

    ingest_res = client.post(
        "/api/v1/ingest/products",
        json={
            "products": [
                {
                    "product_id": 1,
                    "image_url": "https://example.com/1.jpg",
                    "title": "黑色马丁靴",
                    "description": "复古风格",
                    "category_ids": [10],
                    "timestamp": 1700000000,
                    "attributes": {"season": "winter"},
                },
                {
                    "product_id": 2,
                    "image_url": "https://example.com/2.jpg",
                    "title": "棕色马丁靴",
                    "description": "秋冬穿搭",
                    "category_ids": [10],
                    "timestamp": 1700000001,
                    "attributes": {"season": "autumn"},
                },
            ]
        },
    )
    assert ingest_res.status_code == 200

    similar_res = client.post(
        "/api/v1/retrieval/similar",
        json={"product_id": 1, "top_k": 5, "category_filter": []},
    )
    assert similar_res.status_code == 200
    body = similar_res.json()
    assert "request_id" in body
    assert "latency_ms" in body
    assert len(body["results"]) >= 1


def test_text_search_and_hash_update() -> None:
    client = _build_client()

    # Must ingest first so MIH index is non-empty.
    client.post(
        "/api/v1/ingest/products",
        json={
            "products": [
                {
                    "product_id": 100,
                    "image_url": "https://example.com/100.jpg",
                    "title": "长款大衣",
                    "description": "秋冬通勤",
                    "category_ids": [12],
                    "timestamp": 1700001000,
                    "attributes": {},
                }
            ]
        },
    )

    text_res = client.post(
        "/api/v1/retrieval/text-search",
        json={"query_text": "适合秋冬的大衣", "top_k": 5, "category_filter": []},
    )
    assert text_res.status_code == 200
    assert "results" in text_res.json()

    update_res = client.post(
        "/api/v1/hash/update",
        json={
            "mode": "scph",
            "samples": [
                {
                    "product_id": 1,
                    "image_feature": [0.1, 0.2, 0.3, 0.4],
                    "text_feature": None,
                    "label": 1,
                }
            ],
        },
    )
    assert update_res.status_code == 200


def test_similar_image_retrieval() -> None:
    client = _build_client()
    client.post(
        "/api/v1/ingest/products",
        json={
            "products": [
                {
                    "product_id": 300,
                    "image_url": "https://example.com/300.jpg",
                    "title": "测试商品",
                    "description": "用于图片相似检索",
                    "category_ids": [8],
                    "timestamp": 1700003000,
                    "attributes": {},
                }
            ]
        },
    )

    res = client.post(
        "/api/v1/retrieval/similar-image?top_k=3",
        files={"image": ("demo.jpg", b"fake-image-binary", "image/jpeg")},
    )
    assert res.status_code == 200
    assert "results" in res.json()


def test_replay_ingest_endpoint() -> None:
    client = _build_client()
    container = client.app.state.container
    container.queue.publish_product(
        {
            "product_id": 8888,
            "image_url": "https://example.com/8888.jpg",
            "title": "回放测试商品",
            "description": "来自队列回放",
            "category_ids": [9],
            "timestamp": 1700088888,
            "attributes": {},
        }
    )

    res = client.post(
        "/api/v1/ingest/replay",
        json={"max_messages": 10, "timeout_seconds": 1.0},
    )
    assert res.status_code == 200
    assert "consumed=" in res.json()["message"]
