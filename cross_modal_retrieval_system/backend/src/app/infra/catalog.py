from app.schemas.ingest import ProductIngestRecord


class ProductCatalog:
    def __init__(self) -> None:
        self._products: dict[int, ProductIngestRecord] = {}

    def upsert(self, product: ProductIngestRecord) -> None:
        self._products[product.product_id] = product

    def get(self, product_id: int) -> ProductIngestRecord | None:
        return self._products.get(product_id)
