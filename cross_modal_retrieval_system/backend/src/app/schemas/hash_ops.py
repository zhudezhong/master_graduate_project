from pydantic import BaseModel, Field


class HashUpdateSample(BaseModel):
    product_id: int
    image_feature: list[float]
    text_feature: list[float] | None = None
    label: int


class HashUpdateRequest(BaseModel):
    mode: str = Field(pattern="^(scph|mih)$")
    samples: list[HashUpdateSample]
