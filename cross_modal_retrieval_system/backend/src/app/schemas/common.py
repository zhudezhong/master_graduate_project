from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RetrievalItem(BaseModel):
    product_id: int
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid4().hex)
    latency_ms: int
    results: list[RetrievalItem]
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid4().hex)
    message: str
