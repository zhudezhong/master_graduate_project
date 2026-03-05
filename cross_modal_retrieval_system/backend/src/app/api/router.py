from fastapi import APIRouter

from app.api.routes import hash_ops, health, ingest, retrieval

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(hash_ops.router, prefix="/hash", tags=["hash"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
