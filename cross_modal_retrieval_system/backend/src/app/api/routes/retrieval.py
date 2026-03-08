from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_container
from app.infra.container import AppContainer
from app.schemas.retrieval import ProductDisplayItem, SimilarRetrievalRequest, TextSearchRequest

router = APIRouter()


@router.get("/products", response_model=list[ProductDisplayItem])
def list_products(
    limit: int = 12,
    container: AppContainer = Depends(get_container),
):
    safe_limit = max(1, min(limit, 100))
    return container.retrieval_service.list_products_for_display(limit=safe_limit)


@router.post("/similar-image")
async def similar_by_image(
    image: UploadFile = File(...),
    top_k: int = 20,
    container: AppContainer = Depends(get_container),
):
    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="image must not be empty")
    try:
        return container.retrieval_service.similar_by_uploaded_image(
            image_bytes=content,
            filename=image.filename or "uploaded_image",
            top_k=top_k,
            category_filter=[],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/similar-product")
def similar_by_product(
    req: SimilarRetrievalRequest,
    container: AppContainer = Depends(get_container),
):
    try:
        return container.retrieval_service.similar_by_product_id(
            product_id=req.product_id,
            top_k=req.top_k,
            category_filter=req.category_filter,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/text-search")
def text_search(
    req: TextSearchRequest,
    container: AppContainer = Depends(get_container),
):
    try:
        return container.retrieval_service.text_to_image(
            query_text=req.query_text,
            top_k=req.top_k,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/photo-search")
async def photo_search(
    image: UploadFile = File(...),
    top_k: int = 20,
    container: AppContainer = Depends(get_container),
):
    _ = await image.read()
    image_url = image.filename or "upload_image"
    try:
        return container.retrieval_service.image_to_image_cross(image_url=image_url, top_k=top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
