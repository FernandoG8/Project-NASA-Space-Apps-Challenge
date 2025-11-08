# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, analyze, metadata, series
from app.routers import auth, docs_test  # ⬅️ agrega estos

# --- Sub-API que vivirá bajo /api ---
api = FastAPI(
    title="Weather API",
    version="1.0.0",
    description="Probabilidades históricas y clasificación por factores climáticos (POWER / MERRA-ready).",
    docs_url="/docs",             # → /api/docs
    openapi_url="/openapi.json",  # → /api/openapi.json
    redoc_url=None,
)
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if api.openapi_schema:
        return api.openapi_schema
    openapi_schema = get_openapi(
        title=api.title,
        version=api.version,
        description=api.description,
        routes=api.routes,
    )
    openapi_schema["servers"] = [{"url": "/api"}]  # base relativa
    api.openapi_schema = openapi_schema
    return api.openapi_schema

api.openapi = custom_openapi


# Routers dentro de la sub-API
api.include_router(health.router)                   # GET  /api/health
api.include_router(metadata.router, prefix="/v1")   # /api/v1/*
api.include_router(analyze.router,  prefix="/v1")   # /api/v1/analyze
api.include_router(series.router,   prefix="/v1")   # /api/v1/series/*

# 🔐 auth y 🔧 test (ya definidos con prefix interno '/v1/...'):
api.include_router(auth.router)       # tiene prefix="/v1/auth" adentro
api.include_router(docs_test.router)  # tiene prefix="/v1/test" adentro

# --- App raíz (solo contenedor de la sub-API) ---
app = FastAPI()

if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount("/api", api)
