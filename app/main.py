# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, analyze, metadata
from app.routers import analyze, metadata, series

app = FastAPI(
    title="Weather API",
    version="1.0.0",
    description="Probabilidades históricas y clasificación por factores climáticos (POWER / MERRA-ready).",
)

# CORS
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Routers
app.include_router(health.router)                 # GET /health
app.include_router(metadata.router, prefix="/v1") # GET /v1/metadata, /v1/factors
app.include_router(analyze.router,  prefix="/v1") # POST /v1/analyze
app.include_router(series.router, prefix="/v1")   # POST /v1/series 
