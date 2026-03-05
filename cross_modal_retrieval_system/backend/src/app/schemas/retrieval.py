from pydantic import BaseModel, Field


class SimilarRetrievalRequest(BaseModel):
    product_id: int
    top_k: int = Field(default=20, ge=1, le=200)
    category_filter: list[int] = Field(default_factory=list)


class TextSearchRequest(BaseModel):
    query_text: str
    top_k: int = Field(default=20, ge=1, le=200)
    category_filter: list[int] = Field(default_factory=list)
