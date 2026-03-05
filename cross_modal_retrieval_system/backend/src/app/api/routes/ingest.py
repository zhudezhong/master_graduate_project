from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.infra.container import AppContainer
from app.schemas.common import MessageResponse
from app.schemas.ingest import ProductIngestRequest, ReplayIngestRequest

router = APIRouter()


@router.post("/products", response_model=MessageResponse)
def ingest_products(
    req: ProductIngestRequest,
    container: AppContainer = Depends(get_container),
) -> MessageResponse:
    ret = container.ingest_service.ingest_products(req.products)
    return MessageResponse(message=f"accepted={ret['accepted']}, queued={ret['queued']}")


@router.post("/replay", response_model=MessageResponse)
def replay_from_queue(
    req: ReplayIngestRequest,
    container: AppContainer = Depends(get_container),
) -> MessageResponse:
    ret = container.ingest_service.replay_from_queue(
        max_messages=req.max_messages,
        timeout_seconds=req.timeout_seconds,
    )
    return MessageResponse(
        message=(
            f"consumed={ret['consumed']}, "
            f"validated={ret['validated']}, "
            f"indexed={ret['indexed']}"
        )
    )
