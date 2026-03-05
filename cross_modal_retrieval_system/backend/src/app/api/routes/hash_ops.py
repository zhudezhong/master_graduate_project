import torch
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.infra.container import AppContainer
from app.schemas.common import MessageResponse
from app.schemas.hash_ops import HashUpdateRequest

router = APIRouter()


@router.post("/update", response_model=MessageResponse)
def update_hash_model(
    req: HashUpdateRequest,
    container: AppContainer = Depends(get_container),
) -> MessageResponse:
    if not req.samples:
        raise HTTPException(status_code=400, detail="samples must not be empty")
    x_img = torch.tensor([x.image_feature for x in req.samples], dtype=torch.float32)
    y = torch.tensor([x.label for x in req.samples], dtype=torch.long)

    if req.mode == "scph":
        ret = container.hash_service.update_scph(x_img, y)
        return MessageResponse(message=f"mode={ret.mode}, samples={ret.num_samples}")

    text_feats = [x.text_feature for x in req.samples if x.text_feature is not None]
    if len(text_feats) != len(req.samples):
        raise HTTPException(status_code=400, detail="mode=mih requires text_feature")
    x_txt = torch.tensor(text_feats, dtype=torch.float32)
    ids = torch.tensor([x.product_id for x in req.samples], dtype=torch.long)
    ret = container.hash_service.update_mih(x_img, x_txt, y, ids)
    return MessageResponse(message=f"mode={ret.mode}, samples={ret.num_samples}, tables={ret.num_tables}")
