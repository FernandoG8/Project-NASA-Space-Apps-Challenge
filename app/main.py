from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config (por tu estructura actual está en services/)
from app.config import settings

# Routers
from app.routers import health, metadata, probability, compare,  daily,export

app = FastAPI(title="S2S Historical Probability API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,  # propiedad o lista según tu config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas

app.include_router(daily.router, prefix="/v1")
app.include_router(export.router, prefix="/v1")
app.include_router(health.router)             # /health
app.include_router(metadata.router, prefix="/v1")
app.include_router(probability.router, prefix="/v1")
app.include_router(compare.router, prefix="/v1")

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
