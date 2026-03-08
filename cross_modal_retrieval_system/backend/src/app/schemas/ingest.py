from pydantic import BaseModel, Field


class ProductIngestRecord(BaseModel):
    product_id: int
    image_url: str = ""
    title: str
    description: str = ""
    category_ids: list[int] = Field(default_factory=list)
    industry_id: int | None = None
    timestamp: int
    attributes: dict[str, str] = Field(default_factory=dict)


class ProductIngestRequest(BaseModel):
    products: list[ProductIngestRecord]


class ReplayIngestRequest(BaseModel):
    max_messages: int = Field(default=100, ge=1, le=2000)
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)
