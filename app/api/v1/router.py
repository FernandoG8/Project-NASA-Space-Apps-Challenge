"""Version 1 API router."""
from fastapi import APIRouter

from app.api.v1.routes import analyze, auth, docs_test, health, metadata, series


api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(metadata.router)
api_v1_router.include_router(analyze.router)
api_v1_router.include_router(series.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(docs_test.router)

__all__ = ["api_v1_router"]
