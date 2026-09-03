from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .gemini_client import gemini_available
from .routers import agents, documents, investigations, sources
from .seed import run_seed

app = FastAPI(
    title="VeriScope AI",
    description="Agentic research verification API -- Question to validated Answer Contract.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations.router)
app.include_router(documents.router)
app.include_router(sources.router)
app.include_router(agents.router)


@app.on_event("startup")
def on_startup() -> None:
    run_seed()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "gemini_enabled": gemini_available(),
        "postgres_enabled": settings.postgres_enabled,
    }
