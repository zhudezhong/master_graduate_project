from fastapi.testclient import TestClient

from app.main import create_app


def main() -> None:
    app = create_app()
    client = TestClient(app)

    ingest_payload = {
        "products": [
            {
                "product_id": 11,
                "image_url": "https://example.com/11.jpg",
                "title": "短款羽绒服",
                "description": "秋冬保暖",
                "category_ids": [20],
                "timestamp": 1700001111,
                "attributes": {"brand": "demo"},
            },
            {
                "product_id": 12,
                "image_url": "https://example.com/12.jpg",
                "title": "连帽羽绒服",
                "description": "防风轻便",
                "category_ids": [20],
                "timestamp": 1700001112,
                "attributes": {"brand": "demo"},
            },
        ]
    }
    print("POST /ingest/products")
    print(client.post("/api/v1/ingest/products", json=ingest_payload).json())

    print("POST /retrieval/text-search")
    print(
        client.post(
            "/api/v1/retrieval/text-search",
            json={"query_text": "秋冬羽绒服", "top_k": 3, "category_filter": []},
        ).json()
    )


if __name__ == "__main__":
    main()
